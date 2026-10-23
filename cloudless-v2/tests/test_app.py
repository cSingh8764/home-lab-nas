from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

import auth
import main
import storage
from conftest import USERNAME, PASSWORD, upload

PROTECTED = [
    ("get", "/dashboard"),
    ("post", "/upload"),
    ("get", "/download/x.txt"),
    ("post", "/delete/x.txt"),
    ("post", "/create-folder"),
]

# ---------- login ----------

def test_login_success_sets_hardened_cookie(client):
    r = client.post("/login", data={"username": USERNAME, "password": PASSWORD})
    assert r.status_code == 303
    assert r.headers["location"] == "/dashboard"
    cookie = r.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert f"Max-Age={auth.TOKEN_EXPIRE_MINUTES * 60}" in cookie


@pytest.mark.parametrize("username, password", [
    (USERNAME, "wrong-password"),
    ("nobody", "wrong-password"),
])
def test_failed_login_gives_one_generic_error(client, username, password):
    r = client.post("/login", data={"username": username, "password": password})
    assert r.status_code == 200
    assert "Invalid username or password" in r.text
    assert "session" not in r.cookies


def test_dummy_hash_password_never_logs_in(client):
    # the dummy password is public in auth.py; an unknown user must still fail
    r = client.post("/login", data={"username": "nobody", "password": "dummy-password-never-matches"})
    assert "Invalid username or password" in r.text

# ---------- sessions ----------

@pytest.mark.parametrize("method, url", PROTECTED)
def test_protected_routes_redirect_without_session(client, method, url):
    r = getattr(client, method)(url)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def make_token(username, secret, minutes):
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode({"sub": username, "exp": exp}, secret, algorithm=auth.ALGORITHM)


@pytest.mark.parametrize("token", [
    make_token(USERNAME, "cloudless-secret-key-change-this-later", 60),  # the old leaked key
    make_token(USERNAME, auth.SECRET_KEY, -1),                           # expired
    make_token("deleted-user", auth.SECRET_KEY, 60),                     # user not in the DB
    "not-a-jwt",
])
def test_invalid_tokens_are_rejected(client, token):
    client.cookies.set("session", token)
    r = client.get("/dashboard")
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_logout_clears_cookie(logged_in):
    r = logged_in.post("/logout")
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    assert "Max-Age=0" in r.headers["set-cookie"]
    assert logged_in.get("/dashboard").status_code == 303

# ---------- files and folders ----------

def test_upload_list_download_delete(logged_in, sandbox):
    assert upload(logged_in, "notes.txt", b"hello").status_code == 303

    page = logged_in.get("/dashboard")
    assert "notes.txt" in page.text and "5 B" in page.text

    r = logged_in.get("/download/notes.txt")
    assert r.status_code == 200 and r.content == b"hello"

    assert logged_in.post("/delete/notes.txt").status_code == 303
    assert not (sandbox / "storage" / "notes.txt").exists()


def test_nested_folders_and_breadcrumbs(logged_in, sandbox):
    logged_in.post("/create-folder", data={"folder_name": "photos"})
    logged_in.post("/create-folder", params={"path": "photos"}, data={"folder_name": "2026"})
    upload(logged_in, "beach.jpg", b"jpg", path="photos/2026")

    page = logged_in.get("/dashboard", params={"path": "photos/2026"})
    assert page.status_code == 200
    assert "beach.jpg" in page.text
    assert 'href="/dashboard?path=photos">photos</a>' in page.text
    assert logged_in.get("/download/photos/2026/beach.jpg").content == b"jpg"


def test_names_with_special_characters(logged_in):
    name = "a b&c#%.txt"
    upload(logged_in, name, b"odd")
    page = logged_in.get("/dashboard")
    assert "a b&amp;c#%.txt" in page.text
    # the link the page renders must actually work
    assert logged_in.get("/download/a%20b%26c%23%25.txt").content == b"odd"
    assert logged_in.post("/delete/a%20b%26c%23%25.txt").status_code == 303


def test_delete_missing_file_shows_full_dashboard(logged_in):
    r = logged_in.post("/delete/ghost.txt")
    assert r.status_code == 404
    assert "ghost.txt does not exist" in r.text
    assert f"Logged in as {USERNAME}" in r.text

# ---------- upload limit ----------

def test_upload_limit_rejects_and_keeps_existing_file(logged_in, sandbox, monkeypatch):
    upload(logged_in, "keep.txt", b"original")
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 10)

    r = upload(logged_in, "keep.txt", b"x" * 100)
    assert r.status_code == 413
    assert (sandbox / "storage" / "keep.txt").read_bytes() == b"original"
    assert not list((sandbox / "storage").glob("*.part"))


def test_no_upload_limit_by_default(logged_in, sandbox):
    assert upload(logged_in, "big.bin", b"x" * 2_000_000).status_code == 303
    assert (sandbox / "storage" / "big.bin").stat().st_size == 2_000_000

# ---------- format_size ----------

@pytest.mark.parametrize("size, expected", [
    (0, "0 B"),
    (1023, "1023 B"),
    (1536, "1.5 KB"),
    (5 * 1024**2, "5.0 MB"),
    (int(1.5 * 1024**3), "1.5 GB"),
])
def test_format_size(size, expected):
    assert storage.format_size(size) == expected

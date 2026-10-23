"""Path traversal regression tests: every attack from step 2 must keep failing.

The `sandbox` fixture puts SECRET_CONTENT in tmp_path/secret.txt, one level ABOVE storage/.
A passing attack would either return that content, or create/delete files outside storage/.

Note: write ".." with an encoded slash (%2F) in URLs. The test client cleans up a literal
"/../" in a URL before sending it, exactly like a browser, so the attack would never arrive.
"""
import pytest

import storage
from conftest import SECRET_CONTENT, upload

# ---------- A. read attacks: the secret must not appear in the response ----------

@pytest.mark.parametrize("url", [
    "/download/..%2Fsecret.txt",
    "/download/..%252Fsecret.txt",   # double-encoded
    "/download/docs%2F..%2F..%2Fsecret.txt",   # into a folder, then out twice
])
def test_download_attacks_are_blocked(logged_in, url):
    r = logged_in.get(url)
    assert r.status_code in (400, 404)
    assert SECRET_CONTENT not in r.text


def test_download_absolute_path_is_blocked(logged_in, sandbox):
    secret = str(sandbox / "secret.txt").replace("\\", "/")
    r = logged_in.get("/download/" + secret.replace("/", "%2F"))
    assert r.status_code in (400, 404)
    assert SECRET_CONTENT not in r.text


@pytest.mark.parametrize("path", ["..", "../..", "docs/../.."])
def test_listing_outside_storage_is_blocked(logged_in, path):
    r = logged_in.get("/dashboard", params={"path": path})
    assert r.status_code == 400
    # a listing shows names, not content: the parent folder would show secret.txt
    assert "secret.txt" not in r.text

# ---------- B. write/delete attacks: nothing may change outside storage/ ----------

def test_upload_with_dotdot_filename_stays_inside_storage(logged_in, sandbox):
    upload(logged_in, "../evil.txt", b"pwned")
    assert not (sandbox / "evil.txt").exists()
    # basename() strips the "../", so the file lands safely inside storage
    assert (sandbox / "storage" / "evil.txt").read_bytes() == b"pwned"


def test_upload_into_parent_path_is_blocked(logged_in, sandbox):
    r = upload(logged_in, "evil.txt", b"pwned", path="..")
    assert r.status_code == 400
    assert not (sandbox / "evil.txt").exists()


def test_upload_cannot_overwrite_file_outside_storage(logged_in, sandbox):
    upload(logged_in, "secret.txt", b"overwritten", path="..")
    assert (sandbox / "secret.txt").read_text() == SECRET_CONTENT


@pytest.mark.parametrize("folder_name", ["../escaped", "..", "a/b", "a\\b"])
def test_create_folder_with_bad_name_is_blocked(logged_in, sandbox, folder_name):
    r = logged_in.post("/create-folder", data={"folder_name": folder_name})
    assert r.status_code == 400
    assert not (sandbox / "escaped").exists()


def test_cannot_delete_storage_root(logged_in, sandbox):
    upload(logged_in, "precious.txt", b"keep me")
    r = logged_in.post("/delete/storage", params={"path": ".."})
    assert r.status_code == 400
    assert (sandbox / "storage" / "precious.txt").exists()


def test_cannot_delete_file_outside_storage(logged_in, sandbox):
    r = logged_in.post("/delete/secret.txt", params={"path": ".."})
    assert r.status_code == 400
    assert (sandbox / "secret.txt").exists()

# ---------- C. safe_path itself ----------

@pytest.mark.parametrize("parts", [
    ("..",),
    ("..", "secret.txt"),
    ("../secret.txt",),
    ("..\\secret.txt",),
    ("docs/../../secret.txt",),
    ("../storage_evil",),   # would pass a naive startswith() check
])
def test_safe_path_rejects_escapes(sandbox, parts):
    with pytest.raises(ValueError, match="Path escapes storage"):
        storage.safe_path(*parts)


def test_safe_path_rejects_absolute_path(sandbox):
    with pytest.raises(ValueError, match="Path escapes storage"):
        storage.safe_path(str(sandbox / "secret.txt"))


@pytest.mark.parametrize("parts, expected_end", [
    (("docs",), "docs"),
    (("docs", "a.txt"), "a.txt"),
    (("docs/../b.txt",), "b.txt"),   # ".." that stays inside storage is fine
])
def test_safe_path_allows_paths_inside_storage(sandbox, parts, expected_end):
    result = storage.safe_path(*parts)
    assert result.startswith(str((sandbox / "storage").resolve()))
    assert result.endswith(expected_end)

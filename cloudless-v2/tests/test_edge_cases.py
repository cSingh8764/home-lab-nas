"""Edge cases found by probing after the main hardening: odd inputs must give a clean page, never a 500."""
import pytest

import storage
from conftest import USERNAME, upload

# ---------- OS errors ----------

def test_dashboard_path_pointing_at_a_file_is_not_found(logged_in):
    upload(logged_in, "notes.txt")
    r = logged_in.get("/dashboard", params={"path": "notes.txt"})
    assert r.status_code == 404
    assert f"Logged in as {USERNAME}" in r.text


def test_upload_into_a_file_is_not_found(logged_in):
    upload(logged_in, "notes.txt")
    assert upload(logged_in, "x.txt", path="notes.txt").status_code == 404

# ---------- names Windows can't store ----------

BAD_NAMES = [
    "a.txt:hidden",   # NTFS alternate data stream
    "bad<>?.txt",
    'quote".txt',
    "pipe|.txt",
    "star*.txt",
    "tab\there.txt",
    "trailing-dot.",
    "trailing-space ",
    "CON",
    "nul.txt",
    "com1",
    "LPT9.log",
    "x" * 251,
]


@pytest.mark.parametrize("name", BAD_NAMES)
def test_check_name_rejects_invalid_windows_names(name):
    with pytest.raises(ValueError, match="Invalid name"):
        storage.check_name(name)


# the test client percent-encodes '"' and control characters in upload filenames,
# so those two can't arrive through an upload; check_name and create-folder cover them
@pytest.mark.parametrize("name", [n for n in BAD_NAMES if n not in ('quote".txt', "tab\there.txt")])
def test_upload_with_invalid_windows_name_is_rejected(logged_in, sandbox, name):
    r = upload(logged_in, name)
    assert r.status_code == 400
    assert list((sandbox / "storage").iterdir()) == []   # nothing half-created


@pytest.mark.parametrize("name", BAD_NAMES)
def test_create_folder_with_invalid_windows_name_is_rejected(logged_in, sandbox, name):
    r = logged_in.post("/create-folder", data={"folder_name": name})
    assert r.status_code == 400
    assert list((sandbox / "storage").iterdir()) == []


@pytest.mark.parametrize("name", [
    "report.v2.pdf",
    "console.log",     # starts with "con" but isn't a device name
    "COM10",           # only COM1-COM9 are reserved
    ".hidden",
    "a b&c#%.txt",
    "x" * 120,
])
def test_unusual_but_valid_names_are_accepted(logged_in, sandbox, name):
    assert upload(logged_in, name).status_code == 303
    assert (sandbox / "storage" / name).exists()


def test_name_over_full_path_limit_gives_clean_error(logged_in):
    # 250 is a legal name, but on Windows without long paths the full path passes 260 characters
    r = upload(logged_in, "x" * 250)
    assert r.status_code in (303, 400, 404)

# ---------- creating folders ----------

def test_create_existing_folder_shows_message(logged_in):
    logged_in.post("/create-folder", data={"folder_name": "docs"})
    r = logged_in.post("/create-folder", data={"folder_name": "docs"})
    assert r.status_code == 409
    assert "docs already exists" in r.text


def test_create_folder_with_same_name_as_file_shows_message(logged_in, sandbox):
    upload(logged_in, "notes")
    r = logged_in.post("/create-folder", data={"folder_name": "notes"})
    assert r.status_code == 409
    assert (sandbox / "storage" / "notes").is_file()


def test_create_folder_inside_missing_folder_does_not_create_parent(logged_in, sandbox):
    r = logged_in.post("/create-folder", params={"path": "missing"}, data={"folder_name": "child"})
    assert r.status_code == 404
    assert not (sandbox / "storage" / "missing").exists()

# ---------- delete confirmation ----------

def test_delete_buttons_ask_for_confirmation(logged_in):
    upload(logged_in, "notes.txt")
    logged_in.post("/create-folder", data={"folder_name": "docs"})
    page = logged_in.get("/dashboard").text
    assert page.count('onsubmit="return confirmDelete(this)"') == 2
    assert 'data-name="docs" data-kind="folder"' in page
    assert 'data-name="notes.txt" data-kind="file"' in page


def test_name_in_delete_confirmation_cannot_inject_javascript(logged_in):
    evil = "x');alert(1)-.txt"
    upload(logged_in, evil)
    page = logged_in.get("/dashboard").text
    # the name only appears HTML-escaped inside data-name, never inside the onsubmit code
    assert 'data-name="x&#39;);alert(1)-.txt"' in page
    for line in page.splitlines():
        if "onsubmit=" in line:
            assert line.strip().endswith('onsubmit="return confirmDelete(this)">')

"""Edge cases found by probing after the main hardening: odd inputs must give a clean page, never a 500."""
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

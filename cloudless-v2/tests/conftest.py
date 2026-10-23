import os

# must be set before auth is imported; load_dotenv() never overrides an existing variable,
# so tests always use this key instead of the real one in .env
os.environ["CLOUDLESS_SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient

import auth
import database
import main
import storage

USERNAME = "tester"
PASSWORD = "correct-horse"
SECRET_CONTENT = "TOP-SECRET-OUTSIDE-STORAGE"


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A temporary database and storage folder, plus a secret file just OUTSIDE storage.

    tmp_path/
      test.db
      secret.txt      <- traversal tests try to reach this
      storage/        <- STORAGE_DIR
    """
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(storage, "STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", None)

    (tmp_path / "secret.txt").write_text(SECRET_CONTENT)
    database.init_db()
    auth.create_user(USERNAME, PASSWORD)
    return tmp_path


@pytest.fixture
def client(sandbox):
    # the with-block runs the startup event (init_db, creating storage/)
    with TestClient(main.app, follow_redirects=False) as c:
        yield c


@pytest.fixture
def logged_in(client):
    r = client.post("/login", data={"username": USERNAME, "password": PASSWORD})
    assert r.status_code == 303
    return client


def upload(client, name, content=b"hello", path=""):
    return client.post("/upload", params={"path": path}, files={"file": (name, content)})

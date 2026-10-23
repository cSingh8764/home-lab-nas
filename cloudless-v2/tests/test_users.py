import pytest

import auth
import setup
from conftest import USERNAME, PASSWORD


def run_setup(monkeypatch, argv, inputs=(), passwords=()):
    """Run setup.py's main() with fake command-line args, typed input and hidden password input."""
    inputs, passwords = iter(inputs), iter(passwords)
    monkeypatch.setattr("sys.argv", ["setup.py", *argv])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(passwords))
    return setup.main()

# ---------- auth functions ----------

def test_reset_password(sandbox):
    assert auth.reset_password(USERNAME, "new-pw")
    user = auth.get_user(USERNAME)
    assert auth.verify_password("new-pw", user["password"])
    assert not auth.verify_password(PASSWORD, user["password"])


def test_reset_password_unknown_user(sandbox):
    assert not auth.reset_password("nobody", "x")


def test_delete_and_list_users(sandbox):
    auth.create_user("second", "pw")
    assert auth.list_users() == ["second", USERNAME]
    assert auth.delete_user("second")
    assert not auth.delete_user("second")
    assert auth.list_users() == [USERNAME]

# ---------- setup.py ----------

def test_setup_without_arguments_adds_user(sandbox, monkeypatch):
    assert run_setup(monkeypatch, [], inputs=["alice"], passwords=["pw", "pw"]) == 0
    assert auth.verify_password("pw", auth.get_user("alice")["password"])


def test_setup_asks_again_when_passwords_differ(sandbox, monkeypatch):
    assert run_setup(monkeypatch, ["add", "bob"], passwords=["pw1", "typo", "pw2", "pw2"]) == 0
    assert auth.verify_password("pw2", auth.get_user("bob")["password"])


def test_setup_refuses_duplicate_user(sandbox, monkeypatch, capsys):
    assert run_setup(monkeypatch, ["add", USERNAME]) == 1
    assert "already exists" in capsys.readouterr().out


def test_setup_reset_password(sandbox, monkeypatch):
    assert run_setup(monkeypatch, ["reset-password", USERNAME], passwords=["fresh", "fresh"]) == 0
    assert auth.verify_password("fresh", auth.get_user(USERNAME)["password"])


def test_setup_delete_needs_username_typed_again(sandbox, monkeypatch):
    assert run_setup(monkeypatch, ["delete", USERNAME], inputs=["oops"]) == 1
    assert auth.get_user(USERNAME)
    assert run_setup(monkeypatch, ["delete", USERNAME], inputs=[USERNAME]) == 0
    assert not auth.get_user(USERNAME)


def test_deleted_user_session_stops_working(sandbox, logged_in, monkeypatch):
    assert logged_in.get("/dashboard").status_code == 200
    run_setup(monkeypatch, ["delete", USERNAME], inputs=[USERNAME])
    assert logged_in.get("/dashboard").status_code == 303


def test_setup_list(sandbox, monkeypatch, capsys):
    assert run_setup(monkeypatch, ["list"]) == 0
    assert capsys.readouterr().out.strip() == USERNAME

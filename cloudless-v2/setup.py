"""Manage Cloudless users from the server.

  python setup.py                         add a user (same as "add")
  python setup.py add [username]
  python setup.py reset-password [username]
  python setup.py delete <username>
  python setup.py list
"""
import argparse
import getpass
import sys

from database import init_db
import auth


def ask_password() -> str:
    # getpass hides what you type, so the password never shows on screen
    while True:
        password = getpass.getpass("Password: ")
        if not password:
            print("Password can't be empty.")
        elif password != getpass.getpass("Repeat password: "):
            print("Passwords don't match, try again.")
        else:
            return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Cloudless users")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("add", help="create a user").add_argument("username", nargs="?")
    sub.add_parser("reset-password", help="set a new password").add_argument("username", nargs="?")
    sub.add_parser("delete", help="delete a user").add_argument("username")
    sub.add_parser("list", help="list usernames")
    args = parser.parse_args()

    init_db()
    command = args.command or "add"

    if command == "list":
        users = auth.list_users()
        print("\n".join(users) if users else "No users yet.")
        return 0

    username = getattr(args, "username", None) or input("Username: ").strip()
    if not username:
        print("Username can't be empty.")
        return 1

    if command == "add":
        if auth.get_user(username):
            print(f"User '{username}' already exists. Use: python setup.py reset-password {username}")
            return 1
        auth.create_user(username, ask_password())
        print(f"Created user '{username}'.")

    elif command == "reset-password":
        if not auth.get_user(username):
            print(f"No user named '{username}'.")
            return 1
        auth.reset_password(username, ask_password())
        print(f"Password changed for '{username}'. Their existing sessions stay valid until they expire.")

    elif command == "delete":
        if input(f"Delete user '{username}'? Type the username again to confirm: ").strip() != username:
            print("Cancelled.")
            return 1
        if not auth.delete_user(username):
            print(f"No user named '{username}'.")
            return 1
        print(f"Deleted user '{username}'. Their sessions stop working immediately.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

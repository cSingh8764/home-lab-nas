# Cloudless v2

A self-hosted NAS (Network Attached Storage) system built to understand 
how cloud storage platforms like Google Drive work under the hood.

---

## Why I Built This

I was frustrated paying monthly fees for cloud storage while my data still 
lived on someone else's servers. I wanted to understand how these systems 
actually work by building one myself — from authentication to file storage.

---

## Project Goal

This project was built as a learning exercise to explore:

- How file storage systems work
- How authentication is implemented in real applications
- How backend APIs handle state, security, and persistence

Instead of relying on third-party services, this is a simplified system 
built from scratch.

---

## Screenshots

<!-- Add screenshots to docs/screenshots/ and uncomment:
![Login page](docs/screenshots/login.png)
![Dashboard with folders and files](docs/screenshots/dashboard.png)
-->

---

## Features

- Login with bcrypt-hashed passwords and JWT sessions
- Upload files with a progress bar, download, delete
- Folders with breadcrumb navigation
- Human-readable file sizes
- Logout
- Optional upload size limit
- Automated test suite (112 tests)

---

## System Design

The system is structured into three main layers:

**Authentication Layer** (`auth.py`)
- Password hashing using bcrypt
- Signed JWT stored in an HttpOnly session cookie
- A single `current_user` dependency protects every route

**API Layer** (`main.py`)
- Built with FastAPI
- Handles all user requests and file operations

**Storage Layer** (`storage.py`, `database.py`)
- Files stored locally on the server, under `storage/`
- Every path goes through `safe_path()`, which keeps it inside `storage/`
- User accounts stored in SQLite

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python |
| Backend Framework | FastAPI |
| Server | Uvicorn |
| Database | SQLite |
| Password Hashing | passlib + bcrypt |
| Authentication | python-jose (JWT) |
| Configuration | python-dotenv |
| File Uploads | python-multipart |
| Testing | pytest |

---

## How to Run

**1. Clone the repository**
```bash
git clone https://github.com/cSingh8764/home-lab-nas.git
cd home-lab-nas/cloudless-v2
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

**3. Create your `.env` file**

Copy the template, then put a random secret key in it:
```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```
Paste the printed value after `CLOUDLESS_SECRET_KEY=` in `.env`. The app refuses 
to start without it. Never commit `.env`. It's already in `.gitignore`.

| Setting | Default | Meaning |
|---------|---------|---------|
| `CLOUDLESS_SECRET_KEY` | *(required)* | Signs session tokens. Anyone who has it can log in as any user. |
| `CLOUDLESS_SECURE_COOKIES` | `false` | Set to `true` when serving over HTTPS. |
| `CLOUDLESS_MAX_UPLOAD_MB` | *(empty, no limit)* | Maximum upload size in MB. |

**4. Create your user**
```bash
python setup.py
```
Passwords are hidden while you type. The same script manages users later:

| Command | What it does |
|---------|--------------|
| `python setup.py add [username]` | Create a user (also what plain `python setup.py` does) |
| `python setup.py reset-password [username]` | Set a new password, for example if you forgot yours |
| `python setup.py delete <username>` | Delete a user. You type the name again to confirm, and their sessions stop working immediately. |
| `python setup.py list` | List all usernames |

**5. Start the server**
```bash
uvicorn main:app --reload
```

**6. Open in browser**
```
http://127.0.0.1:8000
```

**Run the tests**
```bash
pip install -r requirements-dev.txt
python -m pytest
```
The tests use a temporary database and storage folder, so they never touch your real files.

---

## Security

I hardened this project by finding real vulnerabilities in my own code, exploiting them,
and then fixing them. Each fix has its own commit, and the attacks are now automated tests
that must keep failing.

| Threat | What an attacker could do | Defense |
|--------|---------------------------|---------|
| **Path traversal** | Request `/download/..%2F.env` to read files outside `storage/`, including the secret key and the user database | `safe_path()` resolves the full path (`realpath`), then requires it to be inside `storage/` (`commonpath`, not a string `startswith`). Single names can't contain `/`, `\` or `..`. The storage root can't be deleted. |
| **Forged sessions** | The JWT signing key was hardcoded and public on GitHub, so anyone could sign a token for any user | The key comes from `.env` and is never committed. The app won't start without it. The old key was replaced, so tokens signed with it are rejected. |
| **Username enumeration** | Different errors ("User not found" vs. "Incorrect password"), a crash, and a 3 ms vs. 175 ms timing gap revealed which usernames exist | One generic error. Unknown users are checked against a dummy bcrypt hash, so both failures take the same time. |
| **Forgotten auth checks** | A route that skips the session check is public | Every protected route declares `Depends(current_user)`. Tokens for deleted users are rejected too. |
| **Cookie theft / CSRF** | Scripts reading the session cookie; other sites submitting forms as you | `HttpOnly`, `SameSite=Lax`, `Max-Age` matching the token, optional `Secure` |
| **Leaked data in git** | The SQLite database (with password hashes) was committed | `cloudless.db`, `.env` and `storage/` are untracked and ignored. The affected passwords were changed. |

The `tests/test_traversal.py` suite was checked by deliberately breaking `safe_path()`.
It catches a missing check, a naive `startswith()` check, and a check that rejects everything.

---

## Known Limitations

This is a learning project, not production-ready:

- **Shared storage:** all users see and can change the same files. There are no per-user folders or permissions.
- **Logout doesn't revoke tokens:** logout deletes the cookie in *your* browser. A token copied
  before logout stays valid until it expires (60 minutes). The only way to end all sessions at once is to change `CLOUDLESS_SECRET_KEY`.
- **Upload limit is checked late:** FastAPI's `UploadFile` receives the whole request body before the
  handler runs, so the size limit protects disk space, not bandwidth. This also applies to users who aren't logged in.
  For real protection, add a body-size limit in a reverse proxy (for example nginx `client_max_body_size`).
- **No HTTPS built in:** run it behind a reverse proxy with TLS, and set `CLOUDLESS_SECURE_COOKIES=true`.
- **No rate limiting:** login attempts aren't throttled.
- Files are stored unencrypted, without versioning or recovery.

---

## What I Learned

This project helped me move from theory to implementation:

- How JWT authentication works in practice, and why the signing key is the whole security model
- Why password hashing is critical and how bcrypt works
- How path traversal works, and why you check the resolved path instead of looking for `..`
- How information leaks through error messages and response timing
- How file uploads work over HTTP
- How APIs are structured in real applications
- Basics of SQL and data persistence
- Writing tests that prove a security fix works, and checking those tests by breaking the code on purpose

---

## Future Improvements

- Per-user storage and file sharing via links or permissions
- Token revocation on logout (a per-user token version or a sessions table)
- Rate limiting on login
- GitHub Actions workflow that runs the tests on every push
- Encryption for stored data
- Deployment on a dedicated NAS machine behind HTTPS
- Logging and monitoring

---

## Disclaimer

This is a learning project and should not be used to store sensitive or 
critical data without additional security hardening.

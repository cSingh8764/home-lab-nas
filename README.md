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

## Features (MVP)

- User authentication (login system)
- Upload files to the server
- Download stored files
- Delete files from storage
- Persistent storage of user data and files

---

## System Design

The system is structured into three main layers:

**Authentication Layer**
- Password hashing using bcrypt
- Token-based authentication using JWT

**API Layer**
- Built with FastAPI
- Handles all user requests and file operations

**Storage Layer**
- Files stored locally on the server
- Metadata managed using SQLite

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
| File Uploads | python-multipart |

---

## How to Run

**1. Clone the repository**
```bash
git clone https://github.com/cSingh8764/home-lab-nas.git
cd home-lab-nas/cloudless-v2
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create your user**
```bash
py setup.py
```

**4. Start the server**
```bash
uvicorn main:app --reload
```

**5. Open in browser**
```
http://127.0.0.1:8000
```

## What I Learned

This project helped me move from theory to implementation:

- How JWT authentication works in practice
- Why password hashing is critical and how bcrypt works
- How file uploads work over HTTP
- How APIs are structured in real applications
- Basics of SQL and data persistence
- Managing files on a server

---

## Limitations

This is an MVP and not production-ready:

- Files are stored locally (no distributed storage)
- No encryption for stored files
- No file versioning or recovery
- Basic authentication only
- Not optimized for scale or performance

---

## Future Improvements

- File and folder hierarchy support
- File sharing via links or permissions
- Encryption for stored data
- Deployment on a dedicated NAS machine
- Improved frontend UI/UX
- Logging and monitoring

---

## Disclaimer

This is a learning project and should not be used to store sensitive or 
critical data without additional security hardening.

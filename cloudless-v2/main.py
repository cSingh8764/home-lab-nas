from fastapi import FastAPI, Request, Form, UploadFile, File, Query, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from database import init_db
from urllib.parse import quote
import auth
import os
import storage

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# auth already ran load_dotenv(), so .env values are available here
SECURE_COOKIES = os.getenv("CLOUDLESS_SECURE_COOKIES", "false").lower() == "true"
MAX_UPLOAD_MB = os.getenv("CLOUDLESS_MAX_UPLOAD_MB")
MAX_UPLOAD_BYTES = int(MAX_UPLOAD_MB) * 1024 * 1024 if MAX_UPLOAD_MB else None

@app.on_event("startup")
def startup_event():
    init_db()
    os.makedirs(storage.STORAGE_DIR, exist_ok=True)

# ---------- auth dependency ----------

class NotAuthenticated(Exception):
    pass

def current_user(request: Request) -> str:
    # every protected route declares Depends(current_user), so none can forget the check
    token = request.cookies.get("session")
    username = auth.verify_token(token) if token else None

    # a valid token for a deleted user is rejected too
    if not username or not auth.get_user(username):
        raise NotAuthenticated()
    return username

@app.exception_handler(NotAuthenticated)
def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse(url="/", status_code=303)

# ---------- page helpers ----------

def dashboard_url(path: str) -> str:
    return f"/dashboard?path={quote(path)}"

def render_dashboard(request: Request, username: str, path: str = "", error: str | None = None, status_code: int = 200):
    folders, files = storage.list_contents(path)

    parts = path.split("/") if path else []
    breadcrumbs = [] #previously accesed files
    for i, part in enumerate(parts):
        breadcrumbs.append({
            "name": part,
            "path": "/".join(parts[:i+1])
        })

    return templates.TemplateResponse(request, "dashboard.html", {
        "username": username,
        "files": files,
        "folders": folders,
        "current_path": path,
        "breadcrumbs": breadcrumbs,
        "error": error
    }, status_code=status_code)

def error_page(request: Request, message: str, status_code: int):
    # exception handlers can't use Depends, so check the session here
    username = auth.verify_token(request.cookies.get("session") or "")
    if not username:
        return RedirectResponse(url="/", status_code=303)
    return render_dashboard(request, username, error=message, status_code=status_code)

# storage.safe_path / check_name raise ValueError for paths outside storage or bad names
@app.exception_handler(ValueError)
def invalid_path_handler(request: Request, exc: ValueError):
    return error_page(request, "Invalid path or name", 400)

@app.exception_handler(FileNotFoundError)
def not_found_handler(request: Request, exc: FileNotFoundError):
    return error_page(request, "Not found", 404)

@app.exception_handler(storage.FileTooLarge)
def too_large_handler(request: Request, exc: storage.FileTooLarge):
    return error_page(request, f"File too large (max {MAX_UPLOAD_MB} MB)", 413)

# ---------- routes ----------

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = auth.get_user(username)

    # unknown users are checked against a dummy hash so both failures take the same time
    hashed = user["password"] if user else auth.DUMMY_HASH
    ok = auth.verify_password(password, hashed)

    if not user or not ok:
        return templates.TemplateResponse(request, "login.html", {
            "error": "Invalid username or password"
        })

    token = auth.create_token(username)
    response = RedirectResponse(url="/dashboard", status_code=303)
    # httponly: JavaScript can't read the cookie; samesite=lax: other sites can't send it with their forms
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=SECURE_COOKIES,
        max_age=auth.TOKEN_EXPIRE_MINUTES * 60
    )
    return response

@app.post("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="session", httponly=True, samesite="lax", secure=SECURE_COOKIES)
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, path: str = "", username: str = Depends(current_user)):
    return render_dashboard(request, username, path)

@app.post("/upload")
def upload_file(file: UploadFile = File(...), path: str = "", username: str = Depends(current_user)):
    storage.save_file(file, path, max_bytes=MAX_UPLOAD_BYTES)
    return RedirectResponse(url=dashboard_url(path), status_code=303)

@app.get("/download/{filepath:path}")
def download_file(filepath: str, username: str = Depends(current_user)):
    full_path = storage.safe_path(filepath)

    if not os.path.isfile(full_path):
        raise FileNotFoundError(filepath)

    filename = os.path.basename(full_path)

    return FileResponse(path=full_path, filename=filename)

@app.post("/delete/{filename}")
def delete_file(request: Request, filename: str, path: str = "", username: str = Depends(current_user)):
    success = storage.delete_item(filename, path)

    if not success:
        return render_dashboard(request, username, path, error=f"{filename} does not exist", status_code=404)

    return RedirectResponse(url=dashboard_url(path), status_code=303)

@app.post("/create-folder")
def create_folder(folder_name: str = Form(...), path: str = Query(""), username: str = Depends(current_user)):
    storage.create_folder(folder_name, path)
    return RedirectResponse(url=dashboard_url(path), status_code=303)

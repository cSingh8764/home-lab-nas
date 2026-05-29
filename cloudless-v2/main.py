from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from database import init_db
from urllib.parse import unquote
import auth
import os
import storage

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = auth.get_user(username)
    password = auth.verify_password(password, user["password"])
    
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "User not found"
        })
    
    if not password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Incorrect password"
        })
    
    token = auth.create_token(username)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session", value=token, httponly = True) # "httponly = restricts the access of the cookie token. does not allow it to be seen it "
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, path: str = ""):
  token = request.cookies.get("session")

  if not token:
    return RedirectResponse(url="/", status_code=303)
  
  username = auth.verify_token(token)

  if not username:
    return RedirectResponse(url="/", status_code=303)

  folders, files =  storage.list_contents(path)

  parts = path.split("/") if path else []
  breadcrumbs = [] #previously accesed files
  for i, part in enumerate(parts):
    breadcrumbs.append({
      "name": part,
      "path": "/".join(parts[:i+1])
    })
  
  return templates.TemplateResponse("dashboard.html", {
    "request": request,
    "username": username,
    "files": files,
    "folders": folders,
    "current_path": path,
    "breadcrumbs": breadcrumbs
  })

@app.post("/upload")
def upload_file(request: Request, file: UploadFile = File(...), path: str = ""):
    token = request.cookies.get("session")

    if not token or not auth.verify_token(token):
        return RedirectResponse(url="/", status_code=303)

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_size = 100 * 1024 * 1024

    if file_size > max_size:
        folders, files = storage.list_contents(path)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "files": files,
            "folders": folders,
            "current_path": path,
            "breadcrumbs": [],
            "error": f"{file.filename} is too large. Maximum size is 100MB"
        })

    storage.save_file(file, path)
    return RedirectResponse(url=f"/dashboard?path={path}", status_code=303)

@app.get("/download/{filepath:path}")
def download_file(request: Request, filepath: str):
    token = request.cookies.get("session")
    
    if not token or not auth.verify_token(token):
        return RedirectResponse(url="/", status_code=303)
    
    filepath = unquote(filepath)
    full_path = os.path.join("storage", filepath)
    filename = os.path.basename(full_path)
    return FileResponse(path=full_path, filename=filename)
  

@app.post("/delete/{filename}")
def delete_file(request: Request, filename: str, path: str = ""):
    token = request.cookies.get("session")
    
    if not token or not auth.verify_token(token):
        return RedirectResponse(url="/", status_code=303)
    
    filename = unquote(filename)
    success = storage.delete_item(filename, path)
    
    if not success:
        folders, files = storage.list_contents(path)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "files": files,
            "folders": folders,
            "current_path": path,
            "breadcrumbs": [],
            "error": f"{filename} does not exist"
        })
    
    return RedirectResponse(url=f"/dashboard?path={path}", status_code=303)

@app.post("/create-folder")
def create_folder(request: Request, folder_name: str = Form(...), path: str = ""):
  token = request.cookies.get("session")

  if not token or not auth.verify_token(token):
    return RedirectResponse(url="/", status_code=303)
  
  storage.create_folder(folder_name, path)
  return RedirectResponse(url=f"/dashboard?path={path}", status_code = 303)
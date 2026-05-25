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
def dashboard(request: Request):
  token = request.cookies.get("session")

  if not token:
    return RedirectResponse(url="/", status_code=303)
  
  username = auth.verify_token(token)

  if not username:
    return RedirectResponse(url="/", status_code=303)

  
  files = os.listdir("storage")
  return templates.TemplateResponse("dashboard.html", {
    "request": request,
    "files": files,
    "username": username
  })

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
  token = request.cookies.get("session")

  if not token or not auth.verify_token(token):
    return RedirectResponse(url='/', status_code=303)
  
  file.file.seek(0,2)
  file_size = file.file.tell()
  file.file.seek(0)

  max_size = 100 * 1024 * 1024

  if file_size > max_size:
    files = os.listdir("storage")
    return templates.TemplateResponse("dashboard.html", {
      "request": request,
      "files": files,
      "error": f"{file.filename} is too large. Maximum size is 100MB"
    })
  
  filename = storage.save_file(file)
  return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/download/{filename}")
def download_file(request: Request, filename: str):
    token = request.cookies.get("session")
    
    if not token or not auth.verify_token(token):
        return RedirectResponse(url="/", status_code=303)
    
    filename = unquote(filename)
    file_path = storage.get_file_path(filename)
    return FileResponse(path=file_path, filename=filename)
  

@app.post("/delete/{filename}")
def delete_file(request: Request, filename: str):
  token = request.cookies.get("session")
  
  if not token or not auth.verify_token(token):
    return RedirectResponse(url='/', status_code=303)
  
  filename = unquote(filename)
  file_path = storage.get_file_path(filename)

  filename = unquote(filename)
  file_path = storage.get_file_path(filename)

  if not os.path.exists(file_path):
    files = os.listdir("storage")
    return templates.TemplateResponse("dashboard.html", {
      "request": request,
      "files": files,
      "error": f"{filename} does not exist"
    })
  
  os.remove(file_path)
  return RedirectResponse(url="/dashboard", status_code=303)

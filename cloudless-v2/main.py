from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from database import init_db
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
    
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "User not found"
        })
    
    if not auth.verify_password(password, user["password"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Incorrect password"
        })
    
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/setup")
def setup():
  result = auth.create_user("akshat", "123456789")
  return result

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
  files = os.listdir("storage")
  return templates.TemplateResponse("dashboard.html", {
    "request": request,
    "files": files
  })

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
  filename = storage.save_file(file)
  return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/download/{filename}") #{filename} =  called a path parameter. Means that URL is dynamic and it changes based on what we are downloading
def download_file(filename:str):
  file_path = storage.get_file_path(filename)
  return FileResponse(path=file_path, filename=filename)
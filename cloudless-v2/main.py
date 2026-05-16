from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database import init_db
import auth

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
  init_db()

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
  return templates.TemplateResponse("login.html", {"request": request})
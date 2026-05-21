import shutil
import os
from fastapi import UploadFile

STORAGE_DIR = "storage"

def save_file(file: UploadFile) -> str:
  file_path = os.path.join(STORAGE_DIR, file.filename)
  with open(file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
  return file.filename

def list_files() -> list:
  return os.listdir(STORAGE_DIR)

def get_file_path(filename: str) -> str:
  return os.path.join(STORAGE_DIR, filename)
import shutil
import os
from fastapi import UploadFile

STORAGE_DIR = "storage"

def get_full_path(path: str = "") -> str:
  if path:
    return os.path.join(STORAGE_DIR, path)
  return STORAGE_DIR

def list_contents(path: str = ""):
  full_path = get_full_path(path)
  items = os.listdir(full_path)

  folders = []
  files = []

  for item in items:
    item_path = os.path.join(full_path, item)
    if os.path.isdir(item_path):
      folders.append(item)
    else:
      files.append(item)
    
  return folders, files

def save_file(file: UploadFile, path: str= "") -> str:
  full_path = get_full_path(path)
  file_path = os.path.join(full_path, file.filename)

  with open(file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
  
  return file.filename

def create_folder(name: str, path: str="") -> bool:
  full_path = os.path.join(get_full_path(path), name)
  if os.path.exists(full_path):
    return False
  
  os.makedirs(full_path)
  return True

def get_file_path(filename: str, path: str = "") -> str:
  return os.path.join(get_full_path(path), filename)

def delete_item(name: str, path: str = "") -> bool:
  full_path = os.path.join(get_full_path(path), name)
  if not os.path.exists(full_path):
    return False
  if os.path.isdir(full_path):
    shutil.rmtree(full_path)
  else:
    os.remove(full_path)
  
  return True
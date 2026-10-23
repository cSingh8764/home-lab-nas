import shutil
import os
from fastapi import UploadFile

STORAGE_DIR = "storage"

def check_name(name: str) -> str:
  # a single file/folder name: no separators, no "." or ".."
  if not name or name in (".", "..") or "/" in name or "\\" in name:
    raise ValueError("Invalid name")
  return name

def list_contents(path: str = ""):
  full_path = safe_path(path)
  items = os.listdir(full_path)

  folders = []
  files = []

  for item in items:
    item_path = os.path.join(full_path, item)
    if os.path.isdir(item_path):
      folders.append(item)
    else:
      size = os.path.getsize(item_path)
      files.append({
        "name": item,
        "size": format_size(size)
      })

  return folders, files

def format_size(size_bytes: int) -> str:
  if size_bytes < 1024:
    return f"{size_bytes} B"
  elif size_bytes < 1024 * 1024:
    return f"{size_bytes / 1024:.1f} KB"
  elif size_bytes < 1024 * 1024 * 1024:
    return f"{size_bytes / (1024 * 1024):.1f} MB"
  else:
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

class FileTooLarge(Exception):
  pass

CHUNK_SIZE = 1024 * 1024

def save_file(file: UploadFile, path: str= "", max_bytes: int | None = None) -> str:
  # the browser sends the filename, so treat it as attacker-controlled
  filename = check_name(os.path.basename(file.filename or ""))
  file_path = safe_path(path, filename)

  # write to a temp file first, so a failed upload never clobbers an existing file
  tmp_path = file_path + ".part"
  written = 0
  try:
    with open(tmp_path, "wb") as buffer:
      while chunk := file.file.read(CHUNK_SIZE):
        written += len(chunk)
        if max_bytes is not None and written > max_bytes:
          raise FileTooLarge(filename)
        buffer.write(chunk)
    os.replace(tmp_path, file_path)
  except BaseException:
    if os.path.exists(tmp_path):
      os.remove(tmp_path)
    raise

  return filename

def create_folder(name: str, path: str="") -> bool:
  full_path = safe_path(path, check_name(name))
  if os.path.exists(full_path):
    return False

  os.makedirs(full_path)
  return True

def delete_item(name: str, path: str = "") -> bool:
  full_path = safe_path(path, check_name(name))
  # path=".." + name="storage" resolves to the root itself: never delete it
  if full_path == safe_path():
    raise ValueError("Cannot delete storage root")
  if not os.path.exists(full_path):
    return False
  if os.path.isdir(full_path):
    shutil.rmtree(full_path)
  else:
    os.remove(full_path)

  return True

def safe_path(*parts: str) -> str:
  base = os.path.realpath(STORAGE_DIR)

  target = os.path.realpath(os.path.join(base,*parts))

  if os.path.commonpath([base, target]) != base:
    raise ValueError("Path escapes storage")

  return target

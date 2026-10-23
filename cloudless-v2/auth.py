import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from database import get_db, init_db
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# hashed once at startup; login verifies against it for unknown users (timing)
DUMMY_HASH = pwd_context.hash("dummy-password-never-matches")

load_dotenv()
SECRET_KEY = os.environ["CLOUDLESS_SECRET_KEY"]
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

def hash_password(password:str) -> str:
  return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)

def create_user(username: str, password: str):
    conn = get_db()
    hashed = hash_password(password)

    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()

    except Exception as e:
        return {"error": str(e)}

    finally:
        conn.close()

    return {"message": "User created successfully"}

def get_user(username: str):

  conn = get_db()

  user = conn.execute(
      "SELECT * FROM users WHERE username = ?", 
      (username,)
  ).fetchone()
  conn.close()

  return user

def create_token(username: str) -> str:
  expire =  datetime.now(timezone.utc) + timedelta(minutes = TOKEN_EXPIRE_MINUTES)
  payload = {
    "sub": username,
    "exp": expire
  }
  return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> str | None:
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub") #sub = subject (official JWT field name)
  except JWTError:
    return None
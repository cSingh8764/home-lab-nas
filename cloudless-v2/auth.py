from passlib.context import CryptContext
from database import get_db, init_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
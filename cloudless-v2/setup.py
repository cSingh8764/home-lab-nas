from database import init_db
from auth import create_user

print("Setting up Cloudless v2...")

init_db()

username = input("Enter your username: ")
password = input("Enter your password: ")

result = create_user(username, password)
print(result)
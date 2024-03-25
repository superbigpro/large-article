import os
import jwt
import time
from datetime import datetime, timedelta
import hashlib
from dotenv import load_dotenv
import base64
load_dotenv()

DAY = 86400

SECRET = os.environ.get("SECRET")
SALT = os.environ.get("SALT")

async def encToken(user_id):
  end = int(time.time()) + DAY
  info = {
    "id": user_id,
    "type": "auth",
    "role": "user",
    "end": end,
  }
  token = jwt.encode(info, SECRET, algorithm="HS256")
  return token

async def admin_Token(user_id):
  end = int(time.time()) + DAY
  info = {
    "id": user_id,
    "type": "auth",
    "role": "admin",
    "end": end,
  }
  token = jwt.encode(info, SECRET, algorithm="HS256")
  return token

async def authorize(token: str) -> int | None:
  try:
    user_id = int(base64.b64decode(token.split(".")[0]).decode())
  except:
    return None

  return user_id 

async def admin_check_auth(token):
  unix_time = int(time.time())
  try:
    info = jwt.decode(token, SECRET, algorithms="HS256")
    if info["role"] == "admin" and info["end"] > unix_time:
      return info["id"]
    else:
      return False
  except:
    return False

async def hashing_pw(plain_pw):
  return hashlib.sha256((plain_pw + SALT).encode('utf-8')).hexdigest()

import os
import jwt
import time
from datetime import datetime, timedelta
import hashlib
from dotenv import load_dotenv
load_dotenv()

DAY = 86400

SECRET = os.environ.get("SECRET")
salt = os.environ.get("SALT")

def encToken(user_id):
  end = int(time.time()) + DAY
  info = {
    "id": user_id,
    "type": "auth",
    "role": "user",
    "end": end,
  }
  token = jwt.encode(info, SECRET, algorithm="HS256")
  return token

def admin_Token(user_id):
  end = int(time.time()) + DAY
  info = {
    "id": user_id,
    "type": "auth",
    "role": "admin",
    "end": end,
  }
  token = jwt.encode(info, SECRET, algorithm="HS256")
  return token

def check_auth(token):
  unix_time = int(time.time())
  try:
    info = jwt.decode(token, SECRET, algorithms="HS256")
    if info["type"] == "auth" and info["end"] > unix_time:
      return info["id"]
    else:
      return False
  except:
    return False
  
def admin_check_auth(token):
  unix_time = int(time.time())
  try:
    info = jwt.decode(token, SECRET, algorithms="HS256")
    if info["role"] == "admin" and info["end"] > unix_time:
      return info["id"]
    else:
      return False
  except:
    return False

def hashing_pw(plain_pw):
  return hashlib.sha256((plain_pw + salt).encode('utf-8')).hexdigest()

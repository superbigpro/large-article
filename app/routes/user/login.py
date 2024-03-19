from fastapi import FastAPI, HTTPException, Header, Response, APIRouter
from pydantic import BaseModel, constr
from sqlalchemy import func, select
from datetime import datetime 
import sys

router = APIRouter()

from database.core import *
from database.user import * 
from database.application import *
from database.department import *

from tools import *

class Login_example(BaseModel):
    username: str
    password: str
    

@router.post("/api/login", tags=["login"])
async def login(data: Login_example):
    pw = data.password
    hashed_pw = hashing_pw(pw)
    
    async with AsyncSessionLocal() as session:
        user = await session.execute(select(User).filter(User.username == data.username, User.password == hashed_pw))
        user = user.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail="아이디 혹은 비밀번호가 다릅니다.")

    elif user.role == 'admin':
        token = admin_Token(user.id)
        return {"ok": True, "token": token} 
    
    token = encToken(user.id)
    return {"ok": True, "token": token}

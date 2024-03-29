from fastapi import FastAPI, HTTPException, Header, Response, APIRouter
from pydantic import BaseModel, constr
from sqlalchemy import func, select
from datetime import datetime 
import sys

router = APIRouter()

from database.core import *
from database.user import * 

from tools import encToken, hashing_pw

class Login_example(BaseModel):
    username: str
    password: str
    

@router.post("/api/login", tags=["login"])
async def login(data: Login_example):
    hashed_pw = hashing_pw(data.password)
    
    async with AsyncSessionLocal() as session:
        user = await session.execute(select(User).filter(User.username == data.username, User.password == hashed_pw))
        user_info = user.scalars().first()

        if not user_info:
            raise HTTPException(status_code=400, detail="아이디 혹은 비밀번호가 다릅니다.")
        
        token = encToken(user_info.id)
    return {"ok": True, "token": token}

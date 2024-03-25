from fastapi import FastAPI, HTTPException, Header, Response, APIRouter
from pydantic import BaseModel, constr
from sqlalchemy import func, select
from datetime import datetime 
import sys

router = APIRouter()

from database.core import *
from database.user import * 
from AuthService.app.tools import * 

class Register_example(BaseModel):
    username: str
    password: str
    handle_name: str
    re_pw: str

@router.post("/api/register", tags=["register"])
async def register(data: Register_example): 
    if data.password != data.re_pw:
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")
    
    hashed_pw = hashing_pw(data.password)

    async with AsyncSessionLocal() as session:  
        user = await session.execute(select(User).filter(User.username == data.username))
        user_info = user.scalars().first()

        if user_info: 
            raise HTTPException(status_code=400, detail="이미 가입하셨습니다.")
        
        db_user = User( 
            username=data.username,
            password=hashed_pw,
            handle_name=data.handle_name
        )

        session.add(db_user)  
        await session.commit()

        return {"ok": True}

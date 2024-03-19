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

class Register_example(BaseModel):
    username: str
    school_id: str
    password: str
    re_pw: str

@router.post("/api/register", tags=["register"])
async def register(data: Register_example): 
    if data.password != data.re_pw:
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    hashed_pw = hashing_pw(data.password)

    db_user = User( 
        username=data.username,
        password=hashed_pw,
        school_id=data.school_id,
    )

    async with AsyncSessionLocal() as session:  

        user = await session.execute(select(User).filter(User.username == data.username))

        if user: 
            raise HTTPException(status_code=400, detail="이미 가입하셨습니다.")

        session.add(db_user)  
        await session.commit()

    return {"ok": True}

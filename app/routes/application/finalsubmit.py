from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel, constr
from depends import RequireAuth
from sqlalchemy import func, select
from datetime import datetime 
import sys
import asyncio

router = APIRouter()

from database.core import *
from database.user import * 
from database.application import *
from database.department import *

from tools import *

class Application_example(BaseModel):
    bio : str 
    motive : str 
    plan : str 
    which_department : str

@router.post("/api/final_submit", tags=["application"]) # 최종제출 엔드포인트
async def final_submit(data : Application_example, user=Depends(RequireAuth)):
    
    if not user:
        raise HTTPException(status_code=401, message="로그인 후 이용 가능합니다.")

    async with AsyncSessionLocal() as session: 
        result = await session.execute(select(Application).where(User.id == user))
        apply_info = result.scalars().first()
        
        if apply_info.is_submitted == True:
            raise HTTPException(status_code=400, message="이미 제출하셨습니다.")
    
        department_info = await session.execute(select(Department).where(Department.name == data.which_department))
        department_row = department_info.scalars().first()

        if not department_row:
            raise HTTPException(status_code=400, message="존재하지 않는 부서입니다.")
    
        db_value = Application(
            bio = data.bio,
            motive = data.motive,
            plan = data.plan,
            department_id = department_row.id,
            user_id = user,
            last_modified=datetime.now(),
            is_submitted = True
        )
        
        session.add(db_value) 
        await session.commit()

    return {"ok": "True"} 
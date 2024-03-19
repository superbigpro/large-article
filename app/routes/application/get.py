from fastapi import FastAPI, HTTPException, Header, Response, APIRouter
from pydantic import BaseModel, constr
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

@router.get("/api/show_apply", tags=["application"]) # 임시저장 불러오기
async def get_apply(token : str = Header(...)):
    user = check_auth(token)
    
    if not user:
        return {"ok":"False", "message":"토큰이 올바르지 않습니다."}
    
    async with AsyncSessionLocal() as session:
        max_id_subquery = select(
        func.max(Application.id).label('max_id')).filter(Application.user_id == user).group_by(
            Application.department_id
        ).subquery()

        latest_applications_query = select(Application).join(
            max_id_subquery, Application.id == max_id_subquery.c.max_id
        )

        result = await session.execute(latest_applications_query)
        latest_applications = result.scalars().all()

    return {"ok":"True", "value":latest_applications}

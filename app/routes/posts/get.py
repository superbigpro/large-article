from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel, constr
from sqlalchemy import func, select, desc
from datetime import datetime 
import sys
import asyncio
from depends import RequireAuth

router = APIRouter()

from database.core import *
from database.user import * 
from database.posts import *

@router.get("/api/get_posts/{cursor_id}", tags=["posts"]) # 게시글 불러오기 
async def get_apply(userid=Depends(RequireAuth), cursor_id : int = 0):
    
    if not userid:
        return {"ok":"False", "message":"토큰이 올바르지 않습니다."}
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Posts).order_by(desc(Posts.last_modified)))
        res_result = res.scalars().all()

    return {"ok":"True", "value":res_result}

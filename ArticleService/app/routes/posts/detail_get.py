from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel, constr
from sqlalchemy import select
from datetime import datetime 
from depends import RequireAuth

router = APIRouter()

from database.core import *
from database.user import * 
from database.posts import *

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

router = APIRouter()

@router.get("/api/posts/{post_id}", tags=["posts"])  # 게시글 불러오기
async def get_posts(post_id: int = 0, userid=Depends(RequireAuth)):
    if not userid:
        raise HTTPException(status_code=400, detail="토큰이 올바르지 않습니다.")
    
    async with AsyncSessionLocal() as session:
        posts = await session.execute(select(Posts).options(joinedload(Posts.comments)).where(Posts.id == post_id))
        post_info = session.scalars().first()
        return {
            "ok": "True",
            "data": post_info, 
        }


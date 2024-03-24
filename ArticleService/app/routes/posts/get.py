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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import desc

router = APIRouter()

@router.get("/api/get_posts/{cursor_id}", tags=["posts"])  # 게시글 불러오기
async def get_posts(cursor_id: int = 0, userid=Depends(RequireAuth)):
    if not userid:
        raise HTTPException(status_code=400, detail="토큰이 올바르지 않습니다.")
    
    async with AsyncSessionLocal() as session:
        query = select(Posts).where(Posts.id > cursor_id).order_by(Posts.id).limit(10)  
        res = await session.execute(query)
        posts = res.scalars().all()

        next_cursor_id = posts[-1].id if posts else None

        posts_data = [{
            "title": post.title,
            "author": post.author,
            "created_at": post.created_at
        } for post in posts]

        return {
            "ok": "True",
            "posts": posts_data,  
            "next_cursor_id": next_cursor_id
        }


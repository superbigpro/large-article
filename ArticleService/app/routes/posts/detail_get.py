from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel, constr
from sqlalchemy import select, update
from datetime import datetime 
from depends import RequireAuth
from libs.redis import increment_views, get_views

router = APIRouter()

from database.core import *
# from database.user import * 
from database.posts import *

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

router = APIRouter()

@router.get("/api/posts/{post_id}", tags=["posts"])  # 게시글 불러오기
async def get_posts(post_id: int = 0, userid=Depends(RequireAuth)):
    """
    게시글 상세 조회
    
    Args:
        post_id: 조회할 게시글 ID
        
    Returns:
        게시글 상세 정보
    """
    if not userid:
        raise HTTPException(status_code=400, detail="토큰이 올바르지 않습니다.")
    
    current_views = await increment_views(post_id)
    
    async with AsyncSessionLocal() as session:
        posts = await session.execute(select(Posts).options(joinedload(Posts.comments)).where(Posts.id == post_id))
        post_info = posts.scalars().first()
        
        if not post_info:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
            
        # Redis 연결 실패 등으로 조회수를 가져오지 못한 경우
        # DB의 원래 값에 1을 더한 값 사용
        if current_views == 0 and post_info.views > 0:
            current_views = post_info.views + 1
            
        post_info_dict = {
            "id": post_info.id,
            "title": post_info.title,
            "content": post_info.content,
            "picture": post_info.picture,
            "last_modified": post_info.last_modified,
            "is_modified": post_info.is_modified,
            "views": current_views, 
            "hearts": post_info.hearts,
            "user_id": post_info.user_id,
            "comments": [{"id": comment.id, "content": comment.content} for comment in post_info.comments]
        }
        
        return {
            "ok": "True",
            "data": post_info_dict, 
        }


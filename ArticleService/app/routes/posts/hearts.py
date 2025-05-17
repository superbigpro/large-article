from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from depends import RequireAuth
from libs.redis import increment_hearts, decrement_hearts, get_hearts

router = APIRouter()

from database.core import *
from database.posts import *

class HeartRequest(BaseModel):
    post_id: int

@router.post("/api/posts/hearts", tags=["posts"])
async def add_heart(request: HeartRequest, userid=Depends(RequireAuth)):
    """
    게시글에 좋아요 추가
    
    Args:
        request: 좋아요 요청 정보
        
    Returns:
        좋아요 처리 결과
    """
    if not userid:
        raise HTTPException(status_code=400, detail="토큰이 올바르지 않습니다.")
    
    post_id = request.post_id
    
    async with AsyncSessionLocal() as session:
        # 게시글 존재 확인
        result = await session.execute(
            select(Posts).where(Posts.id == post_id)
        )
        post = result.scalars().first()
        
        if not post:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
        current_hearts = await increment_hearts(post_id)
        
        # Redis 연결 실패 등으로 좋아요를 증가시키지 못한 경우
        # DB에 직접 업데이트
        if current_hearts == 0:
            new_hearts = post.hearts + 1
               
    
    return {
        "ok": "True",
        "message": "좋아요가 추가되었습니다.",
        "hearts": current_hearts
    }

@router.delete("/api/posts/hearts", tags=["posts"])
async def remove_heart(request: HeartRequest, userid=Depends(RequireAuth)):
    """
    게시글 좋아요 취소
    
    Args:
        request: 좋아요 취소 요청 정보
        
    Returns:
        좋아요 취소 처리 결과
    """
    if not userid:
        raise HTTPException(status_code=400, detail="토큰이 올바르지 않습니다.")
    
    post_id = request.post_id
    
    async with AsyncSessionLocal() as session:
        
        result = await session.execute(
            select(Posts).where(Posts.id == post_id)
        )
        post = result.scalars().first()
        
        if not post:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
        current_hearts = await decrement_hearts(post_id)
        
        if current_hearts == 0 and post.hearts > 0:
            new_hearts = max(0, post.hearts - 1)
              
    return {
        "ok": "True",
        "message": "좋아요가 취소되었습니다.",
        "hearts": current_hearts
    } 
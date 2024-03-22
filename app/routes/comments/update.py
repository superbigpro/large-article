from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone     
from depends import RequireAuth
from database.core import AsyncSessionLocal
from database.comments import Comments 
from typing import Optional
from sqlalchemy import select

router = APIRouter()

class ApplicationExample(BaseModel):
    content: str

@router.post("/api/comment/update/{post_id}/{comment_id}", tags=["update comments"])
async def submit_apply(data: ApplicationExample, 
                        userid=Depends(RequireAuth),
                        post_id: int = 0,
                        comment_id: int = 0):
    
    if not userid:
        raise HTTPException(status_code=401, detail="로그인 후 이용 가능합니다.")
    
    async with AsyncSessionLocal() as session:
        post = await session.execute(select(Comments.id == comment_id, Comments.post_id == post_id).where())
        post_info = post.scalars().first()
        
        if post_info:
            post_info.content = data.content
            post_info.last_modified = datetime.now(timezone.utc)
            post_info.is_modified = True
        else:
            raise HTTPException(status_code=404, detail="해당 댓글이 없습니다.")
            
        session.add(post_info)
        await session.commit()

    return {"ok": True}

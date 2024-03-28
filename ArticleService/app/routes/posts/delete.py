from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone     
from depends import RequireAuth
from sqlalchemy.future import select 
from sqlalchemy.sql.expression import desc
from database.core import AsyncSessionLocal
# from database.user import User
from database.posts import Posts
from typing import Optional

router = APIRouter()

@router.post("/api/delete/{post_id}", tags=["create posts"])
async def submit_apply(userid=Depends(RequireAuth), post_id: int = 0):
    
    if not userid:
        raise HTTPException(status_code=401, detail="로그인 후 이용 가능합니다.")
    
    async with AsyncSessionLocal() as session:
        post_query = select(Posts).where(Posts.id == post_id)
        post = await session.execute(post_query)
        post_to_delete = post.scalars().first()
        
        if not post_to_delete:
            raise HTTPException(status_code=404, detail="해당 게시글이 없습니다.")
        
        await session.delete(post_to_delete)
        await session.commit()

    return {"ok": True}

from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone     
from depends import RequireAuth
from sqlalchemy.future import select 
from sqlalchemy.sql.expression import desc
from database.core import AsyncSessionLocal
from database.user import User
from database.posts import Posts
from typing import Optional

router = APIRouter()

class PostsExample(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None
    picture: Optional[bytes] = None

@router.put("/api/update/{post_id}", tags=["update posts"])
async def submit_apply(data: PostsExample, userid=Depends(RequireAuth), post_id: int = 0):
    
    if not userid:
        raise HTTPException(status_code=401, detail="로그인 후 이용 가능합니다.")
    
    async with AsyncSessionLocal() as session:

        post = await session.execute(select(Posts).where(Posts.id == post_id))
        post = post.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="해당 게시글이 없습니다.")

        post.title = data.title,
        post.content = data.content,
        post.picture = data.picture,
        post.last_modified = datetime.now(timezone.utc)
    
        session.add(post)
        await session.commit()

        return {"ok": True}

from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone     
from depends import RequireAuth
from database.core import AsyncSessionLocal
from database.comments import Comments 
from typing import Optional
from sqlalchemy import select, delete

router = APIRouter()

class ApplicationExample(BaseModel):
    content: str

@router.post("/api/comment/delete/{post_id}", tags=["delete comments"])
async def submit_apply(data: ApplicationExample, 
                        userid=Depends(RequireAuth),
                        post_id: int = 0):
    
    if not userid:
        raise HTTPException(status_code=401, detail="로그인 후 이용 가능합니다.")
    
    async with AsyncSessionLocal() as session:
        query = select(Comments).where(Comments.id == post_id, Comments.user_id == userid).delete()
        
        await session.execute(query)
        await session.commit()

    return {"ok": True}

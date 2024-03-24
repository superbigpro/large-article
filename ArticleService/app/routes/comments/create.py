from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone     
from depends import RequireAuth
from database.core import AsyncSessionLocal
from database.comments import Comments 
from typing import Optional

router = APIRouter()

class ApplicationExample(BaseModel):
    content: str

@router.post("/api/comment/create/{post_id}", tags=["create comments"])
async def submit_apply(data: ApplicationExample, 
                        userid=Depends(RequireAuth),
                        post_id: int = 0):
    
    if not userid:
        raise HTTPException(status_code=401, detail="로그인 후 이용 가능합니다.")
    
    async with AsyncSessionLocal() as session:
    
        db_value = Comments(
            content=data.content,
            user_id=userid,
            last_modified=datetime.now(timezone.utc),
            post_id=post_id
        )
    
        session.add(db_value)
        await session.commit()

    return {"ok": True}

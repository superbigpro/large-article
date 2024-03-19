from fastapi import FastAPI, HTTPException, Header, Response, APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone     
from depends import RequireAuth
from sqlalchemy.future import select 
from sqlalchemy.sql.expression import desc
from database.core import AsyncSessionLocal
from database.user import User
from app.database.posts import Application
from typing import Optional

router = APIRouter()

class ApplicationExample(BaseModel):
    content: str
    title: str
    picture: Optional[bytes] = None

@router.post("/api/application", tags=["application"])
async def submit_apply(data: ApplicationExample, userid=Depends(RequireAuth)):
    
    if not userid:
        raise HTTPException(status_code=401, detail="로그인 후 이용 가능합니다.")
    
    async with AsyncSessionLocal() as session:
        

        db_value = Application(
            title=data.title,
            content=data.content,
            picture=data.picture,
            user_id=userid,
            last_modified=datetime.now(timezone.utc),
        )
    
        session.add(db_value)
        await session.commit()

    return {"ok": True}

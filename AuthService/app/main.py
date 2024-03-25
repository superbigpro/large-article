from fastapi import FastAPI, Header
from pathlib import Path
from database.core import async_engine, Base  
from routes import include_router
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  

app = FastAPI()

from AuthService.app.tools import check_auth  


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post("/api/authcheck", tags=["authcheck test"])
async def authcheck(token : str = Header(...)):
    user = check_auth(token)
    
    if not user:
        return {"ok": "False"}
    
    return {"received_token": token}

include_router(app)

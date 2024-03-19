from fastapi import FastAPI, Header
from pathlib import Path
from database.core import async_engine, Base  
from routes import include_router
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  

app = FastAPI()

from tools import check_auth  

from routes.application import *
from routes.user import *

from routes.user import router as user_router
from routes.application import router as application_router

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

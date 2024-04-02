from fastapi import FastAPI, Header
from pathlib import Path
from database.core import async_engine, Base  
from routes import include_router
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  

app = FastAPI()

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# include_router(app)

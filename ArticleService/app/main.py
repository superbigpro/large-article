from fastapi import FastAPI
from database.core import async_engine, Base  
from routes import include_router 

app = FastAPI()

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

include_router(app)

from fastapi import FastAPI
from database.core import async_engine, Base  
from routes import include_router 
from rpc import gRPCServer
import asyncio

app = FastAPI()

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    await gRPCServer.run()

if __name__ == "__main__":
    asyncio.run(main(), create_tables())

include_router(app)

from fastapi import FastAPI, Header
from pathlib import Path
from database.core import async_engine, Base  
from routes import include_router
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  
from rpc import gRPCServer
import asyncio

app = FastAPI()

from tools import check_auth  


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post("/api/authcheck", tags=["authcheck test"])
async def authcheck(token : str = Header(...)):
    user = check_auth(token)
    
    if not user:
        return {"ok": "False"}
    
    return {"received_token": token}

async def main():
    await create_tables()
    await gRPCServer.run()

if __name__ == "__main__":
    asyncio.run(main())

include_router(app)

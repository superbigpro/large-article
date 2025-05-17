from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.core import async_engine, Base  
from routes import include_router 
import asyncio
import signal
import sys
import logging
from batch_update import start_batch_update, stop_batch_update
from libs.redis import close_redis_connection, force_flush_backlogs

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 애플리케이션 시작 시 실행
@app.on_event("startup")
async def startup_event():
    logger.info("애플리케이션 시작 중...")
    # 테이블 생성
    await create_tables()
    # 배치 업데이트 서비스 시작
    start_batch_update()
    logger.info("애플리케이션 시작 완료")

# 애플리케이션 종료 시 실행
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션 종료 중...")

    await stop_batch_update()

    try:
        logger.info("메모리 백로그 처리 중...")
        await force_flush_backlogs()
        
    except Exception as e:
        logger.error(f"백로그 처리 실패: {str(e)}")
        
    await close_redis_connection()
    await async_engine.dispose()
    logger.info("애플리케이션 종료 완료")

include_router(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

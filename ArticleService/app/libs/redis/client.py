"""
Redis 클라이언트 모듈

비동기 Redis 연결 및 기본 설정을 관리합니다.
연결 풀 관리 및 실패 처리 로직이 포함되어 있습니다.
"""
import asyncio
import logging
import aioredis
import os
from typing import Optional
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("redis_client")

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", 10))
REDIS_CONNECTION_RETRY = int(os.getenv("REDIS_CONNECTION_RETRY", 5))
REDIS_CONNECTION_TIMEOUT = int(os.getenv("REDIS_CONNECTION_TIMEOUT", 30))
REDIS_KEY_TTL = int(os.getenv("REDIS_KEY_TTL", 86400))  # 기본 TTL: 1일

VIEWS_PREFIX = "views:"
HEARTS_PREFIX = "hearts:"

UPDATE_INTERVAL = int(os.getenv("REDIS_UPDATE_INTERVAL", 60))

redis_client: Optional[aioredis.Redis] = None
pool: Optional[aioredis.ConnectionPool] = None
# Redis 연결 상태
_is_connected = False

async def get_redis_client() -> aioredis.Redis:
    """
    Redis 클라이언트 인스턴스를 반환합니다.
    연결이 없으면 새로 생성하고, 실패 시 재시도합니다.
    
    Returns:
        aioredis.Redis: Redis 클라이언트 인스턴스
    """
    global redis_client, pool, _is_connected
    
    if redis_client is not None and _is_connected:
        return redis_client
    
    retry_count = 0
    while retry_count < REDIS_CONNECTION_RETRY:
        try:
            if pool is None:
                pool = aioredis.ConnectionPool.from_url(
                    f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
                    max_connections=REDIS_POOL_SIZE,
                    decode_responses=True
                )
            
            redis_client = aioredis.Redis(connection_pool=pool)

            await redis_client.ping()
            _is_connected = True
            logger.info(f"Redis 서버({REDIS_HOST}:{REDIS_PORT})에 연결되었습니다.")
            return redis_client
        
        except (aioredis.RedisError, ConnectionError, asyncio.TimeoutError) as e:
            retry_count += 1
            wait_time = min(2 ** retry_count, REDIS_CONNECTION_TIMEOUT)
            logger.warning(f"Redis 연결 실패 ({retry_count}/{REDIS_CONNECTION_RETRY}): {str(e)}. {wait_time}초 후 재시도...")
            await asyncio.sleep(wait_time)
    
    logger.error(f"Redis 연결을 {REDIS_CONNECTION_RETRY}번 시도했으나 실패했습니다.")
    _is_connected = False
    return None

async def close_redis_connection():
    """
    Redis 연결을 정리합니다.
    애플리케이션 종료 시 호출해야 합니다.
    """
    global redis_client, pool, _is_connected
    
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
    
    if pool is not None:
        await pool.disconnect()
        pool = None
    
    _is_connected = False
    logger.info("Redis 연결이 종료되었습니다.") 
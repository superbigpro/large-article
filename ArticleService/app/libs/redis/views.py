"""
게시글 조회수 관련 Redis 유틸리티

조회수 증가, 조회 등의 기능을 제공합니다.
"""
import logging
import asyncio
import time
from collections import defaultdict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis  # aioredis 대신 redis-py 사용
from .client import get_redis_client, VIEWS_PREFIX, REDIS_KEY_TTL

logger = logging.getLogger("redis_views")

# 로컬 메모리 큐 (Redis 실패 시 임시 저장)
# {post_id: count} 형태로 저장
_views_backlog = defaultdict(int)
_backlog_lock = asyncio.Lock()
_last_flush_time = time.time()
_FLUSH_INTERVAL = 30  

async def increment_views(post_id: int) -> int:
    """
    게시글 조회수 증가 (Redis 캐싱)
    
    Args:
        post_id: 게시글 ID
        
    Returns:
        현재 조회수
    """
    key = f"{VIEWS_PREFIX}{post_id}"
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            # Redis 연결 실패 시 로컬 메모리에 백로그 추가
            logger.warning(f"Redis 연결 실패: post_id={post_id} 조회수 증가 요청을 백로그에 추가합니다.")
            return await _add_to_backlog(post_id)
        
        # 조회수 증가 및 조회
        current_views = await redis_client.incr(key)
        
        # TTL 설정 (키가 존재하지 않았을 때만)
        if current_views == 1:
            await redis_client.expire(key, REDIS_KEY_TTL)
        
        # 백로그 처리 시도 (주기적으로)
        if time.time() - _last_flush_time > _FLUSH_INTERVAL:
            asyncio.create_task(_flush_backlog())
            
        return current_views
    
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (조회수 증가): {str(e)}, post_id={post_id}")
        return await _add_to_backlog(post_id)
    except Exception as e:
        logger.error(f"예상치 못한 오류 (조회수 증가): {str(e)}, post_id={post_id}")
        # 다른 오류도 백로그에 추가
        return await _add_to_backlog(post_id)

async def _add_to_backlog(post_id: int) -> int:
    """
    로컬 메모리 백로그에 조회수 증가 요청 추가
    
    Args:
        post_id: 게시글 ID
        
    Returns:
        현재 추정 조회수 (백로그 기준)
    """
    async with _backlog_lock:
        _views_backlog[post_id] += 1
        # 추정 조회수 반환 (실제 DB 조회수는 모름)
        # 이 값은 UI에 표시될 예상 조회수임
        return _views_backlog[post_id]

async def _flush_backlog():
    """
    백로그에 있는 조회수 증가 요청을 Redis에 반영
    주기적으로 또는 필요 시 호출됨
    """
    global _last_flush_time
    
    # 백로그가 비어있으면 처리하지 않음
    if not _views_backlog:
        return
    
    try:
        redis_client = await get_redis_client()
        if redis_client is None:
            logger.warning("백로그 처리 시도 중 Redis 연결 실패")
            return
            
        # 백로그 데이터 복사 및 초기화 (처리 중 새 요청과 경쟁 조건 방지)
        async with _backlog_lock:
            backlog_copy = dict(_views_backlog)
            _views_backlog.clear()
        
        # Redis 파이프라인으로 일괄 처리
        pipeline = redis_client.pipeline()
        for post_id, increment in backlog_copy.items():
            key = f"{VIEWS_PREFIX}{post_id}"
            # 현재 값에 백로그 값을 더함
            pipeline.incrby(key, increment)
            pipeline.expire(key, REDIS_KEY_TTL)
            
        # 일괄 실행
        await pipeline.execute()
        logger.info(f"백로그 처리 성공: {len(backlog_copy)}개 게시글 조회수 업데이트")
        
        _last_flush_time = time.time()
        
    except Exception as e:
        logger.error(f"백로그 처리 실패: {str(e)}")
        # 실패 시 백로그 복원 (다음 시도에서 재처리)
        async with _backlog_lock:
            for post_id, increment in backlog_copy.items():
                _views_backlog[post_id] += increment

async def get_views(post_id: int) -> int:
    """
    게시글 조회수 조회
    
    Args:
        post_id: 게시글 ID
        
    Returns:
        현재 조회수
    """
    key = f"{VIEWS_PREFIX}{post_id}"
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            logger.error(f"Redis 연결 실패: post_id={post_id} 조회수 조회 요청을 처리할 수 없습니다.")
            # 백로그에 있는 값 확인
            async with _backlog_lock:
                if post_id in _views_backlog:
                    return _views_backlog[post_id]
            return 0
        
        # 조회수 조회
        views = await redis_client.get(key)
        
        # Redis 값 + 백로그 값 (있는 경우)
        result = int(views) if views else 0
        async with _backlog_lock:
            if post_id in _views_backlog:
                result += _views_backlog[post_id]
                
        return result
    
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (조회수 조회): {str(e)}, post_id={post_id}")
        # 백로그 값만 반환
        async with _backlog_lock:
            if post_id in _views_backlog:
                return _views_backlog[post_id]
        return 0
    except Exception as e:
        logger.error(f"예상치 못한 오류 (조회수 조회): {str(e)}, post_id={post_id}")
        return 0

async def update_views_directly_to_db(post_id: int, views: int, session: AsyncSession):
    """
    조회수를 직접 DB에 업데이트 (Redis 실패 시 폴백)
    
    Args:
        post_id: 게시글 ID
        views: 설정할 조회수
        session: DB 세션
    """
    from database.posts import Posts
    
    try:
        # DB에 직접 업데이트
        await session.execute(
            update(Posts).where(Posts.id == post_id).values(views=views)
        )
        await session.commit()
        logger.info(f"post_id={post_id}의 조회수({views})를 DB에 직접 업데이트했습니다.")
    except Exception as e:
        logger.error(f"DB 업데이트 실패 (조회수): {str(e)}, post_id={post_id}")
        await session.rollback()

async def force_flush_backlog():
    """
    백로그를 강제로 처리합니다.
    애플리케이션 종료 전 호출해야 합니다.
    """
    logger.info("백로그 강제 처리 시작")
    await _flush_backlog() 
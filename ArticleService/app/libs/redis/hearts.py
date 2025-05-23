"""
게시글 좋아요 관련 Redis 유틸리티

좋아요 증가, 감소, 조회 등의 기능을 제공합니다.
"""
import logging
import asyncio
import time
from collections import defaultdict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis  
from .client import get_redis_client, HEARTS_PREFIX, REDIS_KEY_TTL

logger = logging.getLogger("redis_hearts")

# 로컬 메모리 큐 (Redis 실패 시 임시 저장)
# {post_id: delta} 형태로 저장 (delta는 증가/감소 값의 합)
_hearts_backlog = defaultdict(int)
_backlog_lock = asyncio.Lock()
_last_flush_time = time.time()
_FLUSH_INTERVAL = 30  

async def increment_hearts(post_id: int) -> int:
    """
    게시글 좋아요 수 증가 (Redis 캐싱)
    
    Args:
        post_id: 게시글 ID
        
    Returns:
        현재 좋아요 수
    """
    key = f"{HEARTS_PREFIX}{post_id}"
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            # Redis 연결 실패 시 로컬 메모리에 백로그 추가
            logger.warning(f"Redis 연결 실패: post_id={post_id} 좋아요 증가 요청을 백로그에 추가합니다.")
            return await _add_to_backlog(post_id, 1)
        
        # 좋아요 수 증가 및 조회
        current_hearts = await redis_client.incr(key)
        
        # TTL 설정 (키가 존재하지 않았을 때만)
        if current_hearts == 1:
            await redis_client.expire(key, REDIS_KEY_TTL)
        
        # 백로그 처리 시도 (주기적으로)
        if time.time() - _last_flush_time > _FLUSH_INTERVAL:
            asyncio.create_task(_flush_backlog())
            
        return current_hearts
    
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (좋아요 증가): {str(e)}, post_id={post_id}")
        # Redis 실패 시 백로그에 추가
        return await _add_to_backlog(post_id, 1)
    except Exception as e:
        logger.error(f"예상치 못한 오류 (좋아요 증가): {str(e)}, post_id={post_id}")
        # 다른 오류도 백로그에 추가
        return await _add_to_backlog(post_id, 1)

async def decrement_hearts(post_id: int) -> int:
    """
    게시글 좋아요 수 감소 (Redis 캐싱)
    
    Args:
        post_id: 게시글 ID
        
    Returns:
        현재 좋아요 수 (0 미만으로 내려가지 않음)
    """
    key = f"{HEARTS_PREFIX}{post_id}"
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            # Redis 연결 실패 시 로컬 메모리에 백로그 추가
            logger.warning(f"Redis 연결 실패: post_id={post_id} 좋아요 감소 요청을 백로그에 추가합니다.")
            return await _add_to_backlog(post_id, -1)
        
        # 현재 좋아요 수 조회
        current_hearts = await redis_client.get(key)
        
        if current_hearts and int(current_hearts) > 0:
            # 좋아요 수 감소 및 조회
            new_hearts = await redis_client.decr(key)
            
            # 백로그 처리 시도 (주기적으로)
            if time.time() - _last_flush_time > _FLUSH_INTERVAL:
                asyncio.create_task(_flush_backlog())
                
            return new_hearts
        else:
            # 좋아요가 없거나 0인 경우 0으로 설정
            await redis_client.set(key, 0, ex=REDIS_KEY_TTL)
            return 0
            
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (좋아요 감소): {str(e)}, post_id={post_id}")
        # Redis 실패 시 백로그에 추가 (음수 값이 될 수 있음)
        return await _add_to_backlog(post_id, -1)
    except Exception as e:
        logger.error(f"예상치 못한 오류 (좋아요 감소): {str(e)}, post_id={post_id}")
        return await _add_to_backlog(post_id, -1)

async def _add_to_backlog(post_id: int, delta: int) -> int:
    """
    로컬 메모리 백로그에 좋아요 변경 요청 추가
    
    Args:
        post_id: 게시글 ID
        delta: 변경량 (+1 증가, -1 감소)
        
    Returns:
        현재 추정 좋아요 수 (백로그 기준)
    """
    async with _backlog_lock:
        _hearts_backlog[post_id] += delta
        # 음수가 되지 않도록 보정
        if _hearts_backlog[post_id] < 0:
            _hearts_backlog[post_id] = 0
        # 추정 좋아요 수 반환 (실제 DB 좋아요 수는 모름)
        # 이 값은 UI에 표시될 예상 좋아요 수임
        return _hearts_backlog[post_id]

async def _flush_backlog():
    """
    백로그에 있는 좋아요 변경 요청을 Redis에 반영
    주기적으로 또는 필요 시 호출됨
    """
    global _last_flush_time
    
    # 백로그가 비어있으면 처리하지 않음
    if not _hearts_backlog:
        return
    
    try:
        redis_client = await get_redis_client()
        if redis_client is None:
            logger.warning("백로그 처리 시도 중 Redis 연결 실패")
            return
            
        # 백로그 데이터 복사 및 초기화 (처리 중 새 요청과 경쟁 조건 방지)
        async with _backlog_lock:
            backlog_copy = dict(_hearts_backlog)
            _hearts_backlog.clear()
        
        # Redis 파이프라인으로 일괄 처리
        for post_id, delta in backlog_copy.items():
            key = f"{HEARTS_PREFIX}{post_id}"
            try:
                # 현재 값 조회
                current = await redis_client.get(key)
                current_val = int(current) if current else 0
                
                # 새 값 계산 (음수 안됨)
                new_val = max(0, current_val + delta)
                
                # 값 설정 및 TTL 설정
                await redis_client.set(key, new_val, ex=REDIS_KEY_TTL)
            except Exception as e:
                logger.error(f"개별 좋아요 백로그 처리 실패: {post_id}, {delta}, {str(e)}")
                # 실패 시 해당 항목만 백로그에 복원
                async with _backlog_lock:
                    _hearts_backlog[post_id] += delta
                    
        logger.info(f"좋아요 백로그 처리 성공: {len(backlog_copy)}개 게시글 좋아요 수 업데이트")
        _last_flush_time = time.time()
        
    except Exception as e:
        logger.error(f"좋아요 백로그 처리 실패: {str(e)}")
        # 실패 시 백로그 복원 (다음 시도에서 재처리)
        async with _backlog_lock:
            for post_id, delta in backlog_copy.items():
                _hearts_backlog[post_id] += delta

async def get_hearts(post_id: int) -> int:
    """
    게시글 좋아요 수 조회
    
    Args:
        post_id: 게시글 ID
        
    Returns:
        현재 좋아요 수
    """
    key = f"{HEARTS_PREFIX}{post_id}"
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            logger.error(f"Redis 연결 실패: post_id={post_id} 좋아요 조회 요청을 처리할 수 없습니다.")
            # 백로그에 있는 값 확인
            async with _backlog_lock:
                if post_id in _hearts_backlog:
                    return _hearts_backlog[post_id]
            return 0
        
        # 좋아요 수 조회
        hearts = await redis_client.get(key)
        
        # Redis 값 + 백로그 값 (있는 경우)
        result = int(hearts) if hearts else 0
        async with _backlog_lock:
            if post_id in _hearts_backlog:
                result += _hearts_backlog[post_id]
                # 음수 방지
                result = max(0, result)
                
        return result
        
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (좋아요 조회): {str(e)}, post_id={post_id}")
        # 백로그 값만 반환
        async with _backlog_lock:
            if post_id in _hearts_backlog:
                return max(0, _hearts_backlog[post_id])
        return 0
    except Exception as e:
        logger.error(f"예상치 못한 오류 (좋아요 조회): {str(e)}, post_id={post_id}")
        return 0

async def update_hearts_directly_to_db(post_id: int, hearts: int, session: AsyncSession):
    """
    좋아요 수를 직접 DB에 업데이트 (Redis 실패 시 폴백)
    
    Args:
        post_id: 게시글 ID
        hearts: 설정할 좋아요 수
        session: DB 세션
    """
    from database.posts import Posts
    
    try:
        # DB에 직접 업데이트
        await session.execute(
            update(Posts).where(Posts.id == post_id).values(hearts=hearts)
        )
        await session.commit()
        logger.info(f"post_id={post_id}의 좋아요 수({hearts})를 DB에 직접 업데이트했습니다.")
    except Exception as e:
        logger.error(f"DB 업데이트 실패 (좋아요): {str(e)}, post_id={post_id}")
        await session.rollback()

async def force_flush_backlog():
    """
    백로그를 강제로 처리합니다.
    애플리케이션 종료 전 호출해야 합니다.
    """
    logger.info("좋아요 백로그 강제 처리 시작")
    await _flush_backlog() 
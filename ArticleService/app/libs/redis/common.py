"""
Redis 공통 유틸리티 함수

여러 통계 데이터를 일괄 처리하거나 캐시를 관리하는 함수들을 제공합니다.
"""
import logging
import redis.asyncio as redis  
from typing import Dict, Tuple, Any, List
from .client import get_redis_client, VIEWS_PREFIX, HEARTS_PREFIX, REDIS_KEY_TTL

# 로깅 설정
logger = logging.getLogger("redis_common")

async def get_all_cached_stats() -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    캐시된 모든 조회수와 좋아요 수를 조회
    
    Returns:
        (views_dict, hearts_dict): 조회수와 좋아요 수 딕셔너리
    """
    views_dict = {}
    hearts_dict = {}
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            logger.error("Redis 연결 실패: 캐시된 통계를 조회할 수 없습니다.")
            return {}, {}
        
        # 청크 단위로 views 키 조회 (SCAN 사용)
        cursor = "0"
        views_pattern = f"{VIEWS_PREFIX}*"
        while cursor != 0:
            cursor, keys = await redis_client.scan(cursor=cursor, match=views_pattern, count=100)
            if keys:
                # 파이프라인으로 일괄 조회
                pipeline = redis_client.pipeline()
                for key in keys:
                    pipeline.get(key)
                values = await pipeline.execute()
                
                # 결과 처리
                for i, key in enumerate(keys):
                    if values[i]:
                        post_id = key.split(":")[-1]
                        views_dict[post_id] = int(values[i])
        
        # 청크 단위로 hearts 키 조회 (SCAN 사용)
        cursor = "0"
        hearts_pattern = f"{HEARTS_PREFIX}*"
        while cursor != 0:
            cursor, keys = await redis_client.scan(cursor=cursor, match=hearts_pattern, count=100)
            if keys:
                # 파이프라인으로 일괄 조회
                pipeline = redis_client.pipeline()
                for key in keys:
                    pipeline.get(key)
                values = await pipeline.execute()
                
                # 결과 처리
                for i, key in enumerate(keys):
                    if values[i]:
                        post_id = key.split(":")[-1]
                        hearts_dict[post_id] = int(values[i])
                
        logger.info(f"캐시된 통계 조회 완료: {len(views_dict)}개 조회수, {len(hearts_dict)}개 좋아요 수")
        return views_dict, hearts_dict
        
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (통계 조회): {str(e)}")
        return {}, {}
    except Exception as e:
        logger.error(f"예상치 못한 오류 (통계 조회): {str(e)}")
        return {}, {}

async def clear_cache_for_post(post_id: int) -> bool:
    """
    특정 게시글의 캐시 삭제
    
    Args:
        post_id: 게시글 ID
        
    Returns:
        bool: 삭제 성공 여부
    """
    views_key = f"{VIEWS_PREFIX}{post_id}"
    hearts_key = f"{HEARTS_PREFIX}{post_id}"
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            logger.error(f"Redis 연결 실패: post_id={post_id}의 캐시를 삭제할 수 없습니다.")
            return False
        
        # 캐시 삭제
        await redis_client.delete(views_key)
        await redis_client.delete(hearts_key)
        logger.info(f"post_id={post_id}의 캐시가 삭제되었습니다.")
        return True
        
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (캐시 삭제): {str(e)}, post_id={post_id}")
        return False
    except Exception as e:
        logger.error(f"예상치 못한 오류 (캐시 삭제): {str(e)}, post_id={post_id}")
        return False

async def sync_post_stats(post_id: int, views: int, hearts: int) -> bool:
    """
    게시글의 통계 정보를 Redis에 동기화
    
    Args:
        post_id: 게시글 ID
        views: 조회수
        hearts: 좋아요 수
        
    Returns:
        bool: 동기화 성공 여부
    """
    views_key = f"{VIEWS_PREFIX}{post_id}"
    hearts_key = f"{HEARTS_PREFIX}{post_id}"
    
    try:
        # Redis 클라이언트 가져오기
        redis_client = await get_redis_client()
        if redis_client is None:
            logger.error(f"Redis 연결 실패: post_id={post_id}의 통계를 동기화할 수 없습니다.")
            return False
            
        # 파이프라인으로 한 번에 여러 명령 처리
        pipeline = redis_client.pipeline()
        pipeline.set(views_key, views, ex=REDIS_KEY_TTL)
        pipeline.set(hearts_key, hearts, ex=REDIS_KEY_TTL)
        await pipeline.execute()
        
        logger.info(f"post_id={post_id}의 통계가 Redis에 동기화되었습니다: 조회수={views}, 좋아요={hearts}")
        return True
        
    except redis.RedisError as e:
        logger.error(f"Redis 오류 (통계 동기화): {str(e)}, post_id={post_id}")
        return False
    except Exception as e:
        logger.error(f"예상치 못한 오류 (통계 동기화): {str(e)}, post_id={post_id}")
        return False 
"""
배치 업데이트 모듈

Redis 캐시 데이터를 주기적으로 데이터베이스에 반영합니다.
애플리케이션 종료 시 정상적으로 종료되는 기능을 포함합니다.
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional
from sqlalchemy import update
from database.core import AsyncSessionLocal
from database.posts import Posts
from libs.redis import get_all_cached_stats, UPDATE_INTERVAL, sync_post_stats, close_redis_connection, force_flush_backlogs

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("batch_update")

# 배치 업데이트 작업 상태
_running = False
_batch_task: Optional[asyncio.Task] = None
_last_update_time = None

async def update_db_from_cache():
    """
    Redis 캐시의 데이터를 데이터베이스에 반영하는 배치 작업
    """
    global _last_update_time
    
    try:
        start_time = datetime.now()
        logger.info(f"배치 업데이트 시작: {start_time}")
        
        # 백로그 처리 먼저 수행
        await force_flush_backlogs()
        
        # 캐시된 모든 통계 가져오기
        views_dict, hearts_dict = await get_all_cached_stats()
        
        if not views_dict and not hearts_dict:
            logger.info("캐시된 데이터가 없습니다.")
            return
        
        update_count = 0    
        async with AsyncSessionLocal() as session:
            # 조회수 업데이트
            for post_id, views in views_dict.items():
                try:
                    await session.execute(
                        update(Posts)
                        .where(Posts.id == int(post_id))
                        .values(views=views)
                    )
                    update_count += 1
                except Exception as e:
                    logger.error(f"게시글 {post_id} 조회수 업데이트 실패: {str(e)}")
            
            # 좋아요 수 업데이트
            for post_id, hearts in hearts_dict.items():
                try:
                    await session.execute(
                        update(Posts)
                        .where(Posts.id == int(post_id))
                        .values(hearts=hearts)
                    )
                    update_count += 1
                except Exception as e:
                    logger.error(f"게시글 {post_id} 좋아요 수 업데이트 실패: {str(e)}")
            
            # 변경사항 커밋
            await session.commit()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"배치 업데이트 완료: {update_count}개 항목 업데이트, 소요 시간: {duration:.2f}초")
            _last_update_time = end_time
            
    except Exception as e:
        logger.error(f"배치 업데이트 중 오류 발생: {str(e)}")

async def run_batch_update_loop():
    """
    주기적으로 배치 업데이트를 실행하는 무한 루프
    """
    global _running
    
    _running = True
    logger.info(f"배치 업데이트 서비스 시작 (간격: {UPDATE_INTERVAL}초)")
    
    try:
        while _running:
            await update_db_from_cache()
            
            # 다음 실행까지 대기 (1초 간격으로 중단 가능한 슬립)
            for _ in range(UPDATE_INTERVAL):
                if not _running:
                    break
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("배치 업데이트 태스크가 취소되었습니다.")
    finally:
        _running = False
        # 마지막 업데이트 실행
        try:
            logger.info("애플리케이션 종료 전 최종 업데이트 실행")
            await update_db_from_cache()
            await close_redis_connection()
        except Exception as e:
            logger.error(f"최종 업데이트 실패: {str(e)}")

def start_batch_update():
    """
    배치 업데이트 서비스를 백그라운드 태스크로 시작
    
    Returns:
        asyncio.Task: 배치 업데이트 태스크
    """
    global _batch_task
    
    if _batch_task is not None and not _batch_task.done():
        logger.warning("배치 업데이트 서비스가 이미 실행 중입니다.")
        return _batch_task
    
    loop = asyncio.get_event_loop()
    _batch_task = loop.create_task(run_batch_update_loop())
    
    # 시그널 핸들러 등록
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(handle_shutdown(s)))
    
    return _batch_task

async def handle_shutdown(sig):
    """
    종료 시그널을 처리하는 핸들러
    """
    global _running, _batch_task
    
    logger.info(f"종료 시그널 수신: {sig.name}")
    _running = False
    
    if _batch_task and not _batch_task.done():
        _batch_task.cancel()
        try:
            await _batch_task
        except asyncio.CancelledError:
            pass
    
    logger.info("배치 업데이트 서비스가 종료되었습니다.")

async def stop_batch_update():
    """
    배치 업데이트 서비스를 중지
    """
    await handle_shutdown(signal.SIGTERM)

if __name__ == "__main__":
    # 독립 실행 모드
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_batch_update_loop())
    except KeyboardInterrupt:
        logger.info("키보드 인터럽트로 종료합니다.")
    finally:
        loop.run_until_complete(close_redis_connection())
        loop.close() 
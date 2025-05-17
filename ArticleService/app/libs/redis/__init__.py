from .client import redis_client, UPDATE_INTERVAL, get_redis_client, close_redis_connection
from .views import increment_views, get_views, force_flush_backlog as force_flush_views_backlog
from .hearts import increment_hearts, decrement_hearts, get_hearts, force_flush_backlog as force_flush_hearts_backlog
from .common import get_all_cached_stats, clear_cache_for_post, sync_post_stats

__all__ = [
    'redis_client',
    'get_redis_client',
    'close_redis_connection',
    'UPDATE_INTERVAL',
    'increment_views',
    'get_views',
    'increment_hearts',
    'decrement_hearts',
    'get_hearts',
    'get_all_cached_stats',
    'clear_cache_for_post',
    'sync_post_stats',
    'force_flush_backlogs',
]

async def force_flush_backlogs():
    """
    모든 백로그를 강제로 처리합니다.
    애플리케이션 종료 전 호출해야 합니다.
    """
    await force_flush_views_backlog()
    await force_flush_hearts_backlog() 
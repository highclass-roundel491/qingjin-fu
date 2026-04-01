import json
import logging
import time
from typing import Optional, Any
from redis.asyncio import Redis, ConnectionPool

from .config import settings

logger = logging.getLogger("uvicorn.error")

_pool: Optional[ConnectionPool] = None
_redis: Optional[Redis] = None


async def init_redis() -> Redis:
    global _pool, _redis
    _pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=50,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )
    _redis = Redis(connection_pool=_pool)
    try:
        await _redis.ping()
        logger.info("Redis 连接成功")
    except Exception as e:
        logger.warning(f"Redis 连接失败，将使用降级模式: {e}")
        _redis = None
    return _redis


async def close_redis():
    global _redis, _pool
    if _redis:
        await _redis.aclose()
        _redis = None
    if _pool:
        await _pool.disconnect()
        _pool = None
    logger.info("Redis 连接已关闭")


def get_redis() -> Optional[Redis]:
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    if not _redis:
        return None
    try:
        raw = await _redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.debug(f"Redis GET 失败 [{key}]: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 300):
    if not _redis:
        return
    try:
        await _redis.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)
    except Exception as e:
        logger.debug(f"Redis SET 失败 [{key}]: {e}")


async def cache_delete(key: str):
    if not _redis:
        return
    try:
        await _redis.delete(key)
    except Exception as e:
        logger.debug(f"Redis DEL 失败 [{key}]: {e}")


async def cache_delete_pattern(pattern: str):
    if not _redis:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = await _redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await _redis.delete(*keys)
            if cursor == 0:
                break
    except Exception as e:
        logger.debug(f"Redis DEL pattern 失败 [{pattern}]: {e}")


async def cache_incr(key: str, amount: int = 1) -> Optional[int]:
    if not _redis:
        return None
    try:
        val = await _redis.incrby(key, amount)
        return val
    except Exception as e:
        logger.debug(f"Redis INCR 失败 [{key}]: {e}")
        return None


VIEW_COUNT_PREFIX = "view_count:"
VIEW_COUNT_PENDING_KEY = VIEW_COUNT_PREFIX + "pending"


async def incr_view_count(poem_id: int):
    if not _redis:
        return
    try:
        await _redis.hincrby(VIEW_COUNT_PENDING_KEY, str(poem_id), 1)
    except Exception as e:
        logger.debug(f"Redis 浏览量计数失败 [poem:{poem_id}]: {e}")


async def flush_view_counts() -> dict[int, int]:
    if not _redis:
        return {}
    try:
        if not await _redis.exists(VIEW_COUNT_PENDING_KEY):
            return {}
        flushing_key = f"{VIEW_COUNT_PREFIX}flushing:{int(time.time() * 1000)}"
        try:
            await _redis.rename(VIEW_COUNT_PENDING_KEY, flushing_key)
        except Exception:
            return {}
        counts = await _redis.hgetall(flushing_key)
        await _redis.delete(flushing_key)
        result = {
            int(pid): int(count)
            for pid, count in counts.items()
            if count and int(count) > 0
        }
        return result
    except Exception as e:
        logger.error(f"Redis flush_view_counts 失败: {e}")
        return {}


RATE_LIMIT_PREFIX = "rl:"


async def check_rate_limit(identifier: str, limit: int, window: int = 60) -> bool:
    if not _redis:
        return True
    try:
        key = f"{RATE_LIMIT_PREFIX}{identifier}"
        current = await _redis.get(key)
        if current is not None and int(current) >= limit:
            return False
        pipe = _redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        await pipe.execute()
        return True
    except Exception as e:
        logger.debug(f"Redis 速率限制检查失败: {e}")
        return True

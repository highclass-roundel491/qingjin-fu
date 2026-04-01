import asyncio
from fastapi import APIRouter
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.core.redis_cache import cache_get, cache_set
from app.models.poem import Poem
from app.models.user import User

router = APIRouter()

STATS_CACHE_KEY = "stats:platform"
STATS_TTL = 600


async def _count_poems(dynasty: str | None = None) -> int:
    async with AsyncSessionLocal() as s:
        query = select(func.count()).select_from(Poem)
        if dynasty:
            query = query.where(Poem.dynasty == dynasty)
        result = await s.execute(query)
        return result.scalar() or 0


@router.get("/platform")
async def get_platform_stats():
    cached = await cache_get(STATS_CACHE_KEY)
    if cached:
        return cached

    async def query_users():
        async with AsyncSessionLocal() as s:
            r = await s.execute(select(func.count()).select_from(User))
            return r.scalar() or 0

    total_poems, tang_poems, song_poems, total_users = await asyncio.gather(
        _count_poems(),
        _count_poems("唐"),
        _count_poems("宋"),
        query_users(),
    )

    data = {
        "total_poems": total_poems,
        "tang_poems": tang_poems,
        "song_poems": song_poems,
        "total_users": total_users
    }
    await cache_set(STATS_CACHE_KEY, data, ttl=STATS_TTL)
    return data

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_cache import cache_get, cache_set
from app.models.poet import Poet
from app.models.poem import Poem
from app.schemas.poet import PoetDetail, PoetListItem, PoetListResponse, PoetBriefForPoem

router = APIRouter()


@router.get("", response_model=PoetListResponse)
async def get_poets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dynasty: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"poets:list:{page}:{page_size}:{dynasty or '_'}:{keyword or '_'}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return PoetListResponse(**cached)

    filters = []
    if dynasty:
        filters.append(Poet.dynasty == dynasty)
    if keyword:
        filters.append(Poet.name.contains(keyword))

    count_q = select(func.count(Poet.id))
    data_q = select(Poet)
    for f in filters:
        count_q = count_q.where(f)
        data_q = data_q.where(f)

    total = (await db.execute(count_q)).scalar() or 0
    data_q = data_q.order_by(Poet.influence_score.desc(), Poet.poem_count.desc())
    data_q = data_q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(data_q)).scalars().all()

    items = [PoetListItem.model_validate(r) for r in rows]
    result = {"items": [i.model_dump() for i in items], "total": total}
    await cache_set(cache_key, result, ttl=300)
    return PoetListResponse(**result)


@router.get("/by-name", response_model=Optional[PoetBriefForPoem])
async def get_poet_by_name(
    name: str = Query(..., min_length=1),
    dynasty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"poets:byname:{name}:{dynasty or '_'}"
    cached = await cache_get(cache_key)
    if cached is not None:
        if cached == "__null__":
            return None
        return PoetBriefForPoem(**cached)

    query = select(Poet).where(Poet.name == name)
    if dynasty:
        query = query.where(Poet.dynasty == dynasty)
    query = query.order_by(Poet.influence_score.desc()).limit(1)
    result = await db.execute(query)
    poet = result.scalar_one_or_none()

    if not poet:
        await cache_set(cache_key, "__null__", ttl=120)
        return None

    brief = PoetBriefForPoem.model_validate(poet)
    await cache_set(cache_key, brief.model_dump(), ttl=300)
    return brief


@router.get("/{poet_id}", response_model=PoetDetail)
async def get_poet_detail(
    poet_id: int,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"poets:detail:{poet_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return PoetDetail(**cached)

    query = select(Poet).where(Poet.id == poet_id)
    result = await db.execute(query)
    poet = result.scalar_one_or_none()
    if not poet:
        raise HTTPException(status_code=404, detail="诗人不存在")

    detail = PoetDetail.model_validate(poet)
    await cache_set(cache_key, detail.model_dump(), ttl=300)
    return detail

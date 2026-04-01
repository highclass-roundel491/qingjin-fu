from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.exc import IntegrityError
from typing import Optional
from app.core.database import get_db
from app.core.achievement_sync import sync_user_achievements
from app.core.redis_cache import incr_view_count, cache_get, cache_set, cache_delete_pattern
from app.models.poem import Poem
from app.models.user import User
from app.schemas.poem import PoemListResponse, PoemDetail
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()


def _apply_poem_filters(query, filters):
    for item in filters:
        query = query.where(item)
    return query


async def _resolve_search_condition(
    db: AsyncSession,
    search_type: str,
    keyword: str,
):
    normalized = keyword.strip() or keyword
    if search_type == "title":
        return Poem.title.contains(normalized)
    if search_type == "author":
        # Full author names are common in the UI; prefer the faster exact-match path.
        if len(normalized) >= 2:
            exact_match_query = select(Poem.id).where(Poem.author == normalized).limit(1)
            exact_match = await db.execute(exact_match_query)
            if exact_match.scalar_one_or_none() is not None:
                return Poem.author == normalized
        return Poem.author.contains(normalized)
    return Poem.content.contains(normalized)


async def _get_is_favorited(poem_id: int, current_user: Optional[User], db: AsyncSession) -> bool:
    if not current_user:
        return False

    from app.models.learning import PoemFavorite

    favorite_query = select(PoemFavorite).where(
        and_(
            PoemFavorite.user_id == current_user.id,
            PoemFavorite.poem_id == poem_id
        )
    )
    favorite_result = await db.execute(favorite_query)
    return favorite_result.scalar_one_or_none() is not None

@router.get("/search", response_model=PoemListResponse)
async def search_poems(
    keyword: str = Query(..., min_length=1),
    search_type: str = Query("content", pattern="^(title|author|content)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"poems:search:{search_type}:{keyword}:{page}:{page_size}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)

    filter_condition = await _resolve_search_condition(db, search_type, keyword)

    count_query = select(func.count()).select_from(Poem)
    data_query = select(
        Poem.id,
        Poem.title,
        Poem.author,
        Poem.dynasty,
        Poem.content,
        Poem.category,
        Poem.genre,
        func.coalesce(Poem.view_count, 0).label("view_count"),
        func.coalesce(Poem.favorite_count, 0).label("favorite_count"),
    )

    if filter_condition is not None:
        count_query = count_query.where(filter_condition)
        data_query = data_query.where(filter_condition)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    data_query = data_query.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(data_query)).all()

    items = []
    for row in rows:
        items.append({
            "id": row.id,
            "title": row.title,
            "author": row.author,
            "dynasty": row.dynasty,
            "content": row.content,
            "category": row.category,
            "genre": row.genre,
            "view_count": row.view_count,
            "favorite_count": row.favorite_count,
        })

    response_data = {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    await cache_set(cache_key, response_data, ttl=120)
    return JSONResponse(content=response_data)

@router.get("/random", response_model=PoemDetail)
async def get_random_poem(
    dynasty: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    count_q = select(func.count()).select_from(Poem)
    if dynasty:
        count_q = count_q.where(Poem.dynasty == dynasty)
    total = (await db.execute(count_q)).scalar() or 0
    if total == 0:
        raise HTTPException(status_code=404, detail="没有找到诗词")

    import random as _random
    offset = _random.randint(0, total - 1)
    query = select(Poem)
    if dynasty:
        query = query.where(Poem.dynasty == dynasty)
    query = query.offset(offset).limit(1)
    result = await db.execute(query)
    poem = result.scalar_one_or_none()
    
    if not poem:
        raise HTTPException(status_code=404, detail="没有找到诗词")

    is_favorited = await _get_is_favorited(poem.id, current_user, db)
    
    poem_dict = {
        'id': poem.id,
        'title': poem.title,
        'author': poem.author,
        'dynasty': poem.dynasty,
        'content': poem.content,
        'translation': poem.translation,
        'annotation': poem.annotation,
        'background': poem.background,
        'appreciation': poem.appreciation,
        'category': poem.category,
        'genre': poem.genre,
        'tags': poem.tags,
        'view_count': poem.view_count or 0,
        'favorite_count': poem.favorite_count or 0,
        'created_at': poem.created_at,
        'updated_at': poem.updated_at,
        'is_favorited': is_favorited
    }
    
    return PoemDetail(**poem_dict)

@router.get("", response_model=PoemListResponse)
async def get_poems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dynasty: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[str] = None,
    genre: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"poems:list:{page}:{page_size}:{dynasty or '_'}:{author or '_'}:{category or '_'}:{genre or '_'}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)

    filters = []
    if dynasty:
        filters.append(Poem.dynasty == dynasty)
    if author:
        filters.append(Poem.author == author)
    if category:
        filters.append(Poem.category == category)
    if genre:
        filters.append(Poem.genre == genre)

    count_query = _apply_poem_filters(
        select(func.count()).select_from(Poem),
        filters,
    )
    data_query = select(
        Poem.id,
        Poem.title,
        Poem.author,
        Poem.dynasty,
        Poem.content,
        Poem.category,
        Poem.genre,
        func.coalesce(Poem.view_count, 0).label("view_count"),
        func.coalesce(Poem.favorite_count, 0).label("favorite_count"),
    )
    data_query = _apply_poem_filters(data_query, filters)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    data_query = data_query.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(data_query)).all()

    items = []
    for row in rows:
        items.append({
            "id": row.id,
            "title": row.title,
            "author": row.author,
            "dynasty": row.dynasty,
            "content": row.content,
            "category": row.category,
            "genre": row.genre,
            "view_count": row.view_count,
            "favorite_count": row.favorite_count,
        })

    response_data = {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    await cache_set(cache_key, response_data, ttl=120)
    return JSONResponse(content=response_data)

@router.get("/{poem_id}", response_model=PoemDetail)
async def get_poem_detail(
    poem_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"poems:detail:{poem_id}"
    if current_user is None:
        cached = await cache_get(cache_key)
        if cached is not None:
            return PoemDetail(**cached)

    query = select(Poem).where(Poem.id == poem_id)
    result = await db.execute(query)
    poem = result.scalar_one_or_none()
    
    if not poem:
        raise HTTPException(status_code=404, detail="诗词不存在")

    is_favorited = await _get_is_favorited(poem.id, current_user, db)
    
    poem_dict = {
        'id': poem.id,
        'title': poem.title,
        'author': poem.author,
        'dynasty': poem.dynasty,
        'content': poem.content,
        'translation': poem.translation,
        'annotation': poem.annotation,
        'background': poem.background,
        'appreciation': poem.appreciation,
        'category': poem.category,
        'genre': poem.genre,
        'tags': poem.tags,
        'view_count': poem.view_count or 0,
        'favorite_count': poem.favorite_count or 0,
        'created_at': poem.created_at,
        'updated_at': poem.updated_at,
        'is_favorited': is_favorited
    }
    
    response_data = PoemDetail(**poem_dict)
    if current_user is None:
        await cache_set(cache_key, response_data.model_dump(), ttl=180)
    return response_data

@router.post("/{poem_id}/view")
async def increment_view_count(
    poem_id: int,
    db: AsyncSession = Depends(get_db)
):
    exists_key = f"poems:exists:{poem_id}"
    poem_exists = await cache_get(exists_key)
    if poem_exists is None:
        query = select(Poem.id).where(Poem.id == poem_id)
        result = await db.execute(query)
        poem_exists = result.scalar_one_or_none() is not None
        await cache_set(exists_key, poem_exists, ttl=300)

    if not poem_exists:
        raise HTTPException(status_code=404, detail="诗词不存在")
    
    await incr_view_count(poem_id)
    
    return {"message": "浏览量已更新"}

@router.post("/{poem_id}/favorite")
async def favorite_poem(
    poem_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.learning import PoemFavorite, UserStats
    
    poem_query = select(Poem).where(Poem.id == poem_id)
    poem_result = await db.execute(poem_query)
    poem = poem_result.scalar_one_or_none()
    
    if not poem:
        raise HTTPException(status_code=404, detail="诗词不存在")
    
    check_query = select(PoemFavorite).where(
        and_(
            PoemFavorite.user_id == current_user.id,
            PoemFavorite.poem_id == poem_id
        )
    )
    check_result = await db.execute(check_query)
    existing = check_result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="已收藏该诗词")
    
    favorite = PoemFavorite(
        user_id=current_user.id,
        poem_id=poem_id
    )
    db.add(favorite)
    
    poem.favorite_count = (poem.favorite_count or 0) + 1
    
    stats_query = select(UserStats).where(UserStats.user_id == current_user.id)
    stats_result = await db.execute(stats_query)
    user_stats = stats_result.scalar_one_or_none()
    
    if not user_stats:
        user_stats = UserStats(user_id=current_user.id)
        db.add(user_stats)
    
    user_stats.total_favorites = (user_stats.total_favorites or 0) + 1

    await sync_user_achievements(db, current_user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="已收藏该诗词")

    await cache_delete_pattern("poems:list:*")
    await cache_delete_pattern("poems:search:*")
    await cache_delete_pattern(f"poems:detail:{poem_id}")
    
    return {"message": "收藏成功"}

@router.delete("/{poem_id}/favorite")
async def unfavorite_poem(
    poem_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.learning import PoemFavorite, UserStats
    
    query = select(PoemFavorite).where(
        and_(
            PoemFavorite.user_id == current_user.id,
            PoemFavorite.poem_id == poem_id
        )
    )
    result = await db.execute(query)
    favorite = result.scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="未收藏该诗词")
    
    await db.delete(favorite)
    
    poem_query = select(Poem).where(Poem.id == poem_id)
    poem_result = await db.execute(poem_query)
    poem = poem_result.scalar_one_or_none()
    
    if poem:
        poem.favorite_count = max(0, (poem.favorite_count or 0) - 1)
    
    stats_query = select(UserStats).where(UserStats.user_id == current_user.id)
    stats_result = await db.execute(stats_query)
    user_stats = stats_result.scalar_one_or_none()
    
    if user_stats:
        user_stats.total_favorites = max(0, user_stats.total_favorites - 1)
    
    await db.commit()
    await cache_delete_pattern("poems:list:*")
    await cache_delete_pattern("poems:search:*")
    await cache_delete_pattern(f"poems:detail:{poem_id}")
    
    return {"message": "取消收藏成功"}

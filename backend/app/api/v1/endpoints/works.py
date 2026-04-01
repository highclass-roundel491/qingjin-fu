from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, delete, case
from typing import Optional
from datetime import datetime, timedelta
import random
from app.core.database import get_db
from app.core.achievement_sync import sync_user_achievements
from app.core.redis_cache import cache_get, cache_set
from app.models.work import Work, WorkLike, WorkStatus
from app.models.user import User
from app.schemas.work import (
    WorkCreate, WorkUpdate, WorkResponse, WorkListItem,
    WorkDetailResponse, WorkListResponse,
    WorkRankingItem, WorkRankingResponse,
    WorkPieceRankingItem, WorkPieceRankingResponse,
    AIScoreRequest, AIScoreResponse
)
from app.api.deps import get_current_user, get_current_user_optional
from app.core.levels import calculate_level, calculate_work_publish_exp

router = APIRouter()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_work(
    data: WorkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    work = Work(
        user_id=current_user.id,
        title=data.title,
        content=data.content,
        genre=data.genre,
        status=WorkStatus.DRAFT
    )
    db.add(work)
    await db.commit()
    await db.refresh(work)

    return {
        "code": 201,
        "message": "作品创建成功",
        "data": WorkResponse.from_orm(work).model_dump()
    }


@router.put("/{work_id}", response_model=dict)
async def update_work(
    work_id: int,
    data: WorkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Work).where(and_(Work.id == work_id, Work.user_id == current_user.id))
    )
    work = result.scalar_one_or_none()

    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或无权限编辑")

    if work.status == WorkStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="已发布的作品不能编辑，请先撤回")

    if data.title is not None:
        work.title = data.title
    if data.content is not None:
        work.content = data.content
    if data.genre is not None:
        work.genre = data.genre

    await db.commit()
    await db.refresh(work)

    return {
        "code": 200,
        "message": "作品更新成功",
        "data": WorkResponse.from_orm(work).model_dump()
    }


@router.post("/{work_id}/publish", response_model=dict)
async def publish_work(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Work).where(and_(Work.id == work_id, Work.user_id == current_user.id))
    )
    work = result.scalar_one_or_none()

    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或无权限操作")

    if work.status == WorkStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="作品已发布")

    exp_gained = 0
    if (work.exp_awarded or 0) == 0:
        exp_gained = calculate_work_publish_exp(work.content, work.genre)
        current_user.exp = (current_user.exp or 0) + exp_gained
        current_user.level = calculate_level(current_user.exp)
        work.exp_awarded = exp_gained

    work.status = WorkStatus.PUBLISHED
    work.published_at = func.now()
    await sync_user_achievements(db, current_user)
    await db.commit()
    await db.refresh(work)

    return {
        "code": 200,
        "message": f"作品发布成功，获得{exp_gained}点经验" if exp_gained else "作品发布成功",
        "data": WorkResponse.from_orm(work).model_dump()
    }


@router.post("/{work_id}/unpublish", response_model=dict)
async def unpublish_work(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Work).where(and_(Work.id == work_id, Work.user_id == current_user.id))
    )
    work = result.scalar_one_or_none()

    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或无权限操作")

    if work.status != WorkStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="作品未发布")

    work.status = WorkStatus.DRAFT
    work.published_at = None
    await db.commit()
    await db.refresh(work)

    return {
        "code": 200,
        "message": "作品已撤回至草稿",
        "data": WorkResponse.from_orm(work).model_dump()
    }


@router.delete("/{work_id}", response_model=dict)
async def delete_work(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Work).where(and_(Work.id == work_id, Work.user_id == current_user.id))
    )
    work = result.scalar_one_or_none()

    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或无权限删除")

    await db.execute(delete(WorkLike).where(WorkLike.work_id == work_id))
    await db.execute(delete(Work).where(Work.id == work_id))
    await db.commit()

    return {"code": 200, "message": "作品已删除"}


@router.get("", response_model=dict)
async def get_works(
    sort: str = Query("new", pattern="^(hot|new|score)$"),
    genre: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Work, User.username, User.avatar_url)
        .join(User, Work.user_id == User.id)
        .where(Work.status == WorkStatus.PUBLISHED)
    )

    if genre:
        query = query.where(Work.genre == genre)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    if sort == "hot":
        query = query.order_by(desc(Work.like_count))
    elif sort == "score":
        query = query.order_by(desc(Work.ai_total_score))
    else:
        query = query.order_by(desc(Work.published_at))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    liked_work_ids = set()
    if current_user:
        like_query = select(WorkLike.work_id).where(WorkLike.user_id == current_user.id)
        like_result = await db.execute(like_query)
        liked_work_ids = {r[0] for r in like_result.all()}

    items = []
    for work, username, avatar_url in rows:
        items.append(WorkListItem(
            id=work.id,
            user_id=work.user_id,
            username=username,
            avatar_url=avatar_url,
            title=work.title,
            content=work.content,
            genre=work.genre,
            status=work.status,
            ai_total_score=work.ai_total_score,
            like_count=work.like_count or 0,
            view_count=work.view_count or 0,
            is_liked=work.id in liked_work_ids,
            created_at=work.created_at,
            published_at=work.published_at
        ))

    return {
        "code": 200,
        "data": WorkListResponse(
            items=items, total=total, page=page, page_size=page_size
        ).model_dump()
    }


@router.get("/mine", response_model=dict)
async def get_my_works(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(draft|published)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Work).where(Work.user_id == current_user.id)

    if status_filter:
        query = query.where(Work.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(desc(Work.updated_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    works = result.scalars().all()

    items = []
    for work in works:
        items.append(WorkListItem(
            id=work.id,
            user_id=work.user_id,
            username=current_user.username,
            avatar_url=current_user.avatar_url,
            title=work.title,
            content=work.content,
            genre=work.genre,
            status=work.status,
            ai_total_score=work.ai_total_score,
            like_count=work.like_count or 0,
            view_count=work.view_count or 0,
            is_liked=False,
            created_at=work.created_at,
            published_at=work.published_at
        ))

    return {
        "code": 200,
        "data": WorkListResponse(
            items=items, total=total, page=page, page_size=page_size
        ).model_dump()
    }


@router.get("/rankings", response_model=dict)
async def get_work_rankings(
    period: str = Query("all", pattern="^(daily|weekly|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"works:rankings:{period}:{page}:{page_size}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    query = (
        select(
            Work.user_id,
            User.username,
            User.avatar_url,
            User.exp,
            func.count(Work.id).label("work_count"),
            func.coalesce(func.sum(Work.like_count), 0).label("total_likes"),
            func.avg(Work.ai_total_score).label("avg_score")
        )
        .join(User, Work.user_id == User.id)
        .where(Work.status == WorkStatus.PUBLISHED)
    )

    if period == "daily":
        since = datetime.utcnow() - timedelta(days=1)
        query = query.where(Work.published_at >= since)
    elif period == "weekly":
        since = datetime.utcnow() - timedelta(days=7)
        query = query.where(Work.published_at >= since)

    query = query.group_by(Work.user_id, User.username, User.avatar_url, User.exp)

    count_sub = query.subquery()
    count_q = select(func.count()).select_from(count_sub)
    total_result = await db.execute(count_q)
    total = total_result.scalar()

    query = query.order_by(desc("total_likes")).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for idx, row in enumerate(rows):
        exp = row.exp or 0
        items.append(WorkRankingItem(
            rank=(page - 1) * page_size + idx + 1,
            user_id=row.user_id,
            username=row.username,
            avatar_url=row.avatar_url,
            exp=exp,
            level=calculate_level(exp),
            work_count=row.work_count,
            total_likes=row.total_likes,
            avg_score=round(float(row.avg_score), 1) if row.avg_score else None
        ))

    response_data = {
        "code": 200,
        "data": WorkRankingResponse(items=items, total=total).model_dump()
    }
    await cache_set(cache_key, response_data, ttl=30)
    return response_data


@router.get("/{work_id}", response_model=dict)
async def get_work_detail(
    work_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Work, User.username, User.avatar_url)
        .join(User, Work.user_id == User.id)
        .where(Work.id == work_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="作品不存在")

    work, username, avatar_url = row

    if work.status != WorkStatus.PUBLISHED:
        if not current_user or current_user.id != work.user_id:
            raise HTTPException(status_code=404, detail="作品不存在")

    is_liked = False
    if current_user:
        like_result = await db.execute(
            select(WorkLike).where(
                and_(WorkLike.user_id == current_user.id, WorkLike.work_id == work_id)
            )
        )
        is_liked = like_result.scalar_one_or_none() is not None

    response_data = {
        "code": 200,
        "data": WorkDetailResponse(
            id=work.id,
            user_id=work.user_id,
            username=username,
            avatar_url=avatar_url,
            title=work.title,
            content=work.content,
            genre=work.genre,
            status=work.status,
            ai_grammar_score=work.ai_grammar_score,
            ai_artistic_score=work.ai_artistic_score,
            ai_total_score=work.ai_total_score,
            ai_feedback=work.ai_feedback,
            like_count=work.like_count or 0,
            view_count=(work.view_count or 0) + 1,
            comment_count=work.comment_count or 0,
            is_liked=is_liked,
            created_at=work.created_at,
            updated_at=work.updated_at,
            published_at=work.published_at
        ).model_dump()
    }

    work.view_count = (work.view_count or 0) + 1
    await db.commit()

    return response_data


@router.post("/{work_id}/like", response_model=dict)
async def like_work(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    work_result = await db.execute(select(Work).where(Work.id == work_id))
    work = work_result.scalar_one_or_none()

    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if work.status != WorkStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="只能点赞已发布的作品")

    existing = await db.execute(
        select(WorkLike).where(
            and_(WorkLike.user_id == current_user.id, WorkLike.work_id == work_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已点赞该作品")

    like = WorkLike(user_id=current_user.id, work_id=work_id)
    db.add(like)
    work.like_count = (work.like_count or 0) + 1

    owner_result = await db.execute(select(User).where(User.id == work.user_id))
    owner = owner_result.scalar_one_or_none()
    if owner:
        await sync_user_achievements(db, owner)

    await db.commit()

    return {"code": 200, "message": "点赞成功"}


@router.delete("/{work_id}/like", response_model=dict)
async def unlike_work(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(WorkLike).where(
            and_(WorkLike.user_id == current_user.id, WorkLike.work_id == work_id)
        )
    )
    like = result.scalar_one_or_none()

    if not like:
        raise HTTPException(status_code=404, detail="未点赞该作品")

    await db.delete(like)

    work_result = await db.execute(select(Work).where(Work.id == work_id))
    work = work_result.scalar_one_or_none()
    if work:
        work.like_count = max(0, (work.like_count or 0) - 1)

    await db.commit()

    return {"code": 200, "message": "取消点赞成功"}


def compute_composite_score(like_count: int, ai_total_score: Optional[int], view_count: int) -> float:
    like_score = min(like_count * 2.0, 100.0)
    ai_score = float(ai_total_score) if ai_total_score else 0.0
    view_score = min(view_count * 0.1, 20.0)
    composite = ai_score * 0.5 + like_score * 0.35 + view_score * 0.15
    return round(composite, 2)


@router.get("/rankings/works", response_model=dict)
async def get_work_piece_rankings(
    ranking_type: str = Query("composite", pattern="^(composite|ai_score|popularity)$"),
    period: str = Query("all", pattern="^(daily|weekly|monthly|all)$"),
    genre: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"works:piece-rankings:{ranking_type}:{period}:{genre or '_'}:{page}:{page_size}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    query = (
        select(Work, User.username, User.avatar_url)
        .join(User, Work.user_id == User.id)
        .where(Work.status == WorkStatus.PUBLISHED)
    )

    if period == "daily":
        since = datetime.utcnow() - timedelta(days=1)
        query = query.where(Work.published_at >= since)
    elif period == "weekly":
        since = datetime.utcnow() - timedelta(days=7)
        query = query.where(Work.published_at >= since)
    elif period == "monthly":
        since = datetime.utcnow() - timedelta(days=30)
        query = query.where(Work.published_at >= since)

    if genre:
        query = query.where(Work.genre == genre)

    count_sub = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_sub)
    total = total_result.scalar()

    if ranking_type == "ai_score":
        query = query.order_by(desc(func.coalesce(Work.ai_total_score, 0)), desc(Work.like_count))
    elif ranking_type == "popularity":
        query = query.order_by(desc(Work.like_count), desc(Work.view_count))
    else:
        composite_expr = (
            func.coalesce(Work.ai_total_score, 0) * 0.5 +
            func.least(Work.like_count * 2.0, 100.0) * 0.35 +
            func.least(Work.view_count * 0.1, 20.0) * 0.15
        )
        query = query.order_by(desc(composite_expr))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for idx, (work, username, avatar_url) in enumerate(rows):
        cs = compute_composite_score(
            work.like_count or 0,
            work.ai_total_score,
            work.view_count or 0
        )
        items.append(WorkPieceRankingItem(
            rank=(page - 1) * page_size + idx + 1,
            work_id=work.id,
            title=work.title,
            content=work.content,
            genre=work.genre,
            user_id=work.user_id,
            username=username,
            avatar_url=avatar_url,
            like_count=work.like_count or 0,
            view_count=work.view_count or 0,
            ai_grammar_score=work.ai_grammar_score,
            ai_artistic_score=work.ai_artistic_score,
            ai_total_score=work.ai_total_score,
            composite_score=cs,
            published_at=work.published_at
        ))

    response_data = {
        "code": 200,
        "data": WorkPieceRankingResponse(
            items=items, total=total,
            ranking_type=ranking_type, period=period
        ).model_dump()
    }
    await cache_set(cache_key, response_data, ttl=30)
    return response_data


@router.post("/{work_id}/ai-score", response_model=dict)
async def score_work_with_ai(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Work).where(and_(Work.id == work_id, Work.user_id == current_user.id))
    )
    work = result.scalar_one_or_none()

    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或无权限操作")

    content = work.content
    genre = work.genre

    lines = [l.strip() for l in content.split('\n') if l.strip()]
    line_count = len(lines)

    grammar_base = 70
    if genre in ['五言绝句', '七言绝句']:
        expected_lines = 4
        if line_count == expected_lines:
            grammar_base += 10
        char_per_line = 5 if '五言' in genre else 7
        correct_lines = sum(1 for l in lines if len(l) == char_per_line)
        grammar_base += int(correct_lines / max(line_count, 1) * 15)
    elif genre in ['五言律诗', '七言律诗']:
        expected_lines = 8
        if line_count == expected_lines:
            grammar_base += 10
        char_per_line = 5 if '五言' in genre else 7
        correct_lines = sum(1 for l in lines if len(l) == char_per_line)
        grammar_base += int(correct_lines / max(line_count, 1) * 15)
    else:
        grammar_base += random.randint(5, 20)

    grammar_score = min(grammar_base + random.randint(-3, 5), 100)
    artistic_score = random.randint(60, 95)
    total_score = int(grammar_score * 0.4 + artistic_score * 0.6)

    feedback_parts = []
    if grammar_score >= 85:
        feedback_parts.append("格律严谨，遣词用字工整")
    elif grammar_score >= 70:
        feedback_parts.append("格律基本合规，个别处可再推敲")
    else:
        feedback_parts.append("格律仍有改进空间，建议参考经典作品")

    if artistic_score >= 85:
        feedback_parts.append("意境深远，文采斐然，颇具诗人气韵")
    elif artistic_score >= 70:
        feedback_parts.append("意象选取得当，情感表达较为到位")
    else:
        feedback_parts.append("建议丰富意象层次，加强情感凝练")

    feedback = "；".join(feedback_parts) + "。"

    work.ai_grammar_score = grammar_score
    work.ai_artistic_score = artistic_score
    work.ai_total_score = total_score
    work.ai_feedback = feedback
    await db.commit()
    await db.refresh(work)

    cs = compute_composite_score(
        work.like_count or 0, total_score, work.view_count or 0
    )

    return {
        "code": 200,
        "message": "AI评分完成",
        "data": AIScoreResponse(
            work_id=work.id,
            grammar_score=grammar_score,
            artistic_score=artistic_score,
            total_score=total_score,
            feedback=feedback,
            composite_score=cs
        ).model_dump()
    }

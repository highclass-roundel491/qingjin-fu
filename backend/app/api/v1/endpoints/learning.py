from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct
from datetime import date, datetime, timedelta
from app.core.database import get_db
from app.core.achievement_sync import sync_user_achievements
from app.models.learning import LearningRecord, PoemFavorite, UserStats
from app.models.poem import Poem
from app.models.user import User
from app.models.challenge import ChallengeSubmission
from app.schemas.learning import LearningRecordCreate, UserStatsResponse
from app.schemas.poem import PoemListResponse, PoemListItem
from app.api.deps import get_current_user
from app.core.levels import LEARNING_MIN_DURATION_SECONDS, calculate_learning_exp, calculate_level, get_next_rank

router = APIRouter()

@router.post("/record")
async def record_learning(
    record: LearningRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_first_view = False
    if record.action == "view":
        existing_view_query = select(LearningRecord.id).where(
            and_(
                LearningRecord.user_id == current_user.id,
                LearningRecord.poem_id == record.poem_id,
                LearningRecord.action == "view",
                LearningRecord.duration >= LEARNING_MIN_DURATION_SECONDS
            )
        ).limit(1)
        existing_view_result = await db.execute(existing_view_query)
        is_first_view = existing_view_result.scalar_one_or_none() is None

    new_record = LearningRecord(
        user_id=current_user.id,
        poem_id=record.poem_id,
        action=record.action,
        duration=record.duration
    )
    
    db.add(new_record)
    
    stats_query = select(UserStats).where(UserStats.user_id == current_user.id)
    stats_result = await db.execute(stats_query)
    user_stats = stats_result.scalar_one_or_none()
    
    if not user_stats:
        user_stats = UserStats(user_id=current_user.id, total_learned=0, total_favorites=0, study_time=0, streak_days=0)
        db.add(user_stats)
    await db.flush()

    if record.action == "view":
        user_stats.study_time = (user_stats.study_time or 0) + record.duration

        learned_query = select(func.count(distinct(LearningRecord.poem_id))).where(
            and_(
                LearningRecord.user_id == current_user.id,
                LearningRecord.action == "view",
                LearningRecord.duration >= LEARNING_MIN_DURATION_SECONDS
            )
        )
        learned_result = await db.execute(learned_query)
        user_stats.total_learned = learned_result.scalar() or 0
      
    today = date.today()
    last_study_date = user_stats.last_study_date.date() if user_stats.last_study_date else None
    if last_study_date != today:
        user_stats.last_study_date = datetime.now()
        user_stats.streak_days += 1

    exp_gained = calculate_learning_exp(record.action, is_first_view, record.duration)
    if exp_gained > 0:
        current_user.exp = (current_user.exp or 0) + exp_gained
        current_user.level = calculate_level(current_user.exp)

    await sync_user_achievements(db, current_user)
    
    await db.commit()
    
    return {"message": "学习记录已保存"}

@router.get("/stats", response_model=UserStatsResponse)
async def get_learning_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stats_query = select(UserStats).where(UserStats.user_id == current_user.id)
    stats_result = await db.execute(stats_query)
    user_stats = stats_result.scalar_one_or_none()
    
    if not user_stats:
        user_stats = UserStats(
            user_id=current_user.id,
            total_learned=0,
            total_favorites=0,
            study_time=0,
            streak_days=0
        )
    
    exp = current_user.exp or 0
    level = calculate_level(exp)
    next_rank = get_next_rank(level)
    next_level_exp = next_rank["exp_required"] if next_rank else exp

    return UserStatsResponse(
        total_learned=user_stats.total_learned,
        total_favorites=user_stats.total_favorites,
        study_time=user_stats.study_time,
        streak_days=user_stats.streak_days,
        level=level,
        exp=exp,
        next_level_exp=next_level_exp
    )

@router.get("/favorites", response_model=PoemListResponse)
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Poem).join(PoemFavorite).where(
        PoemFavorite.user_id == current_user.id
    ).order_by(PoemFavorite.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    poems = result.scalars().all()
    
    items = []
    for poem in poems:
        poem_dict = {
            'id': poem.id,
            'title': poem.title,
            'author': poem.author,
            'dynasty': poem.dynasty,
            'content': poem.content,
            'category': poem.category,
            'genre': poem.genre,
            'view_count': poem.view_count or 0,
            'favorite_count': poem.favorite_count or 0
        }
        items.append(PoemListItem(**poem_dict))
    
    return PoemListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/progress")
async def get_learning_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    uid = current_user.id

    async def q_daily():
        r = await db.execute(
            select(
                func.date(LearningRecord.created_at).label('date'),
                func.sum(LearningRecord.duration).label('duration')
            ).where(and_(LearningRecord.user_id == uid, LearningRecord.created_at >= thirty_days_ago))
            .group_by(func.date(LearningRecord.created_at))
            .order_by(func.date(LearningRecord.created_at))
        )
        return [{"date": str(row.date), "duration": row.duration or 0} for row in r.all()]

    async def q_dynasty():
        r = await db.execute(
            select(Poem.dynasty, func.count(distinct(LearningRecord.poem_id)).label('count'))
            .join(Poem, LearningRecord.poem_id == Poem.id)
            .where(LearningRecord.user_id == uid)
            .group_by(Poem.dynasty)
            .order_by(func.count(distinct(LearningRecord.poem_id)).desc())
        )
        return [{"dynasty": row.dynasty or "未知", "count": row.count} for row in r.all()]

    async def q_genre():
        r = await db.execute(
            select(Poem.genre, func.count(distinct(LearningRecord.poem_id)).label('count'))
            .join(Poem, LearningRecord.poem_id == Poem.id)
            .where(and_(LearningRecord.user_id == uid, Poem.genre.isnot(None)))
            .group_by(Poem.genre)
            .order_by(func.count(distinct(LearningRecord.poem_id)).desc())
            .limit(10)
        )
        return [{"genre": row.genre, "count": row.count} for row in r.all()]

    async def q_cumulative():
        r = await db.execute(
            select(
                func.date(LearningRecord.created_at).label('date'),
                func.count(distinct(LearningRecord.poem_id)).label('count')
            ).where(LearningRecord.user_id == uid)
            .group_by(func.date(LearningRecord.created_at))
            .order_by(func.date(LearningRecord.created_at))
        )
        data = []
        total = 0
        for row in r.all():
            total += row.count
            data.append({"date": str(row.date), "total": total})
        return data

    async def q_challenge():
        r = await db.execute(
            select(
                func.avg(ChallengeSubmission.beauty_score).label('beauty_avg'),
                func.avg(ChallengeSubmission.creativity_score).label('creativity_avg'),
                func.avg(ChallengeSubmission.mood_score).label('mood_avg')
            ).where(ChallengeSubmission.user_id == uid)
        )
        row = r.first()
        return {
            "beauty_avg": round(float(row.beauty_avg), 1) if row.beauty_avg else 0,
            "creativity_avg": round(float(row.creativity_avg), 1) if row.creativity_avg else 0,
            "mood_avg": round(float(row.mood_avg), 1) if row.mood_avg else 0
        }

    async def q_calendar():
        r = await db.execute(
            select(
                func.date(LearningRecord.created_at).label('date'),
                func.count().label('activity')
            ).where(and_(LearningRecord.user_id == uid, LearningRecord.created_at >= thirty_days_ago))
            .group_by(func.date(LearningRecord.created_at))
        )
        return [{"date": str(row.date), "activity": row.activity} for row in r.all()]

    import asyncio
    daily, dynasty, genre, cumulative, challenge, calendar = await asyncio.gather(
        q_daily(), q_dynasty(), q_genre(), q_cumulative(), q_challenge(), q_calendar()
    )

    return {
        "daily_study_time": daily,
        "dynasty_distribution": dynasty,
        "genre_distribution": genre,
        "cumulative_learned": cumulative,
        "challenge_performance": challenge,
        "study_calendar": calendar
    }

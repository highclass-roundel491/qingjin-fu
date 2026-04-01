import json
from typing import Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.user import User
from ...models.learning import LearningRecord, PoemFavorite, UserStats
from ...models.poem import Poem
from ...models.challenge import ChallengeSubmission
from ...models.work import Work

GET_USER_PROFILE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_user_profile",
        "description": "获取当前用户的学习画像，包括等级、经验、学习统计、连续学习天数等。适用于个性化推荐、了解用户水平、调整回答难度等场景。需要提供用户ID。",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "用户ID"
                }
            },
            "required": ["user_id"]
        }
    }
}

GET_USER_LEARNING_HISTORY_TOOL = {
    "type": "function",
    "function": {
        "name": "get_user_learning_history",
        "description": "获取用户最近的学习记录，包括学过哪些诗词、收藏了哪些、挑战成绩等。适用于推荐相关诗词、避免重复推荐、了解用户兴趣偏好等场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "用户ID"
                },
                "record_type": {
                    "type": "string",
                    "enum": ["recent_learned", "favorites", "challenge_scores", "works"],
                    "description": "记录类型：recent_learned=最近学习, favorites=收藏, challenge_scores=挑战成绩, works=创作作品",
                    "default": "recent_learned"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量上限，默认10",
                    "default": 10
                }
            },
            "required": ["user_id"]
        }
    }
}


async def tool_get_user_profile(
    db: AsyncSession,
    user_id: int,
) -> str:
    user_q = select(User).where(User.id == user_id)
    user_r = await db.execute(user_q)
    user = user_r.scalar_one_or_none()
    if not user:
        return json.dumps({"error": "用户不存在"}, ensure_ascii=False)

    stats_q = select(UserStats).where(UserStats.user_id == user_id)
    stats_r = await db.execute(stats_q)
    stats = stats_r.scalar_one_or_none()

    fav_count_q = select(func.count(PoemFavorite.id)).where(PoemFavorite.user_id == user_id)
    fav_r = await db.execute(fav_count_q)
    fav_count = fav_r.scalar() or 0

    work_count_q = select(func.count(Work.id)).where(Work.user_id == user_id)
    work_r = await db.execute(work_count_q)
    work_count = work_r.scalar() or 0

    challenge_q = select(func.count(ChallengeSubmission.id), func.avg(ChallengeSubmission.ai_score)).where(
        ChallengeSubmission.user_id == user_id
    )
    ch_r = await db.execute(challenge_q)
    ch_row = ch_r.one()
    challenge_count = ch_row[0] or 0
    avg_score = round(float(ch_row[1]), 1) if ch_row[1] else 0

    fav_cats_q = (
        select(Poem.category, func.count(PoemFavorite.id).label("cnt"))
        .join(Poem, Poem.id == PoemFavorite.poem_id)
        .where(PoemFavorite.user_id == user_id)
        .group_by(Poem.category)
        .order_by(desc("cnt"))
        .limit(5)
    )
    fav_cats_r = await db.execute(fav_cats_q)
    preferred_categories = [{"category": r[0] or "未分类", "count": r[1]} for r in fav_cats_r.all()]

    profile = {
        "nickname": user.nickname or user.username,
        "level": user.level,
        "exp": user.exp,
        "total_learned": stats.total_learned if stats else 0,
        "study_time_minutes": (stats.study_time // 60) if stats else 0,
        "streak_days": stats.streak_days if stats else 0,
        "favorites_count": fav_count,
        "works_count": work_count,
        "challenge_count": challenge_count,
        "avg_challenge_score": avg_score,
        "preferred_categories": preferred_categories,
    }
    return json.dumps(profile, ensure_ascii=False)


async def tool_get_user_learning_history(
    db: AsyncSession,
    user_id: int,
    record_type: str = "recent_learned",
    limit: int = 10,
) -> str:
    cap = min(limit, 20)

    if record_type == "recent_learned":
        q = (
            select(LearningRecord, Poem.title, Poem.author, Poem.dynasty)
            .join(Poem, Poem.id == LearningRecord.poem_id)
            .where(LearningRecord.user_id == user_id)
            .order_by(desc(LearningRecord.created_at))
            .limit(cap)
        )
        r = await db.execute(q)
        rows = r.all()
        items = [
            {
                "title": row[1],
                "author": row[2],
                "dynasty": row[3],
                "action": row[0].action,
                "duration_sec": row[0].duration,
                "time": row[0].created_at.isoformat() if row[0].created_at else "",
            }
            for row in rows
        ]

    elif record_type == "favorites":
        q = (
            select(Poem.title, Poem.author, Poem.dynasty, Poem.category, PoemFavorite.created_at)
            .join(Poem, Poem.id == PoemFavorite.poem_id)
            .where(PoemFavorite.user_id == user_id)
            .order_by(desc(PoemFavorite.created_at))
            .limit(cap)
        )
        r = await db.execute(q)
        items = [
            {
                "title": row[0],
                "author": row[1],
                "dynasty": row[2],
                "category": row[3] or "",
                "favorited_at": row[4].isoformat() if row[4] else "",
            }
            for row in r.all()
        ]

    elif record_type == "challenge_scores":
        q = (
            select(ChallengeSubmission)
            .where(ChallengeSubmission.user_id == user_id)
            .order_by(desc(ChallengeSubmission.submitted_at))
            .limit(cap)
        )
        r = await db.execute(q)
        subs = r.scalars().all()
        items = [
            {
                "answer": s.answer,
                "ai_score": s.ai_score,
                "beauty_score": s.beauty_score,
                "creativity_score": s.creativity_score,
                "time": s.submitted_at.isoformat() if s.submitted_at else "",
            }
            for s in subs
        ]

    elif record_type == "works":
        q = (
            select(Work)
            .where(Work.user_id == user_id)
            .order_by(desc(Work.created_at))
            .limit(cap)
        )
        r = await db.execute(q)
        works = r.scalars().all()
        items = [
            {
                "title": w.title,
                "genre": w.genre,
                "status": w.status,
                "ai_total_score": w.ai_total_score,
                "like_count": w.like_count,
                "time": w.created_at.isoformat() if w.created_at else "",
            }
            for w in works
        ]
    else:
        return json.dumps({"error": f"不支持的记录类型: {record_type}"}, ensure_ascii=False)

    return json.dumps({
        "record_type": record_type,
        "items": items,
        "count": len(items),
    }, ensure_ascii=False)

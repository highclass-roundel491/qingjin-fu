from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.core.achievement_sync import CATEGORY_NAMES, CATEGORY_ORDER, get_user_stat_value, sync_user_achievements
from app.core.levels import get_next_rank
from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.schemas.achievement import (
    AchievementInfo, AchievementCategory, AchievementListResponse,
    UserAchievementItem, UserAchievementResponse,
    AchievementProgressItem, AchievementProgressResponse
)
from app.api.deps import get_current_user

router = APIRouter()


def build_user_achievement_item(user_achievement: UserAchievement, achievement: Achievement) -> UserAchievementItem:
    return UserAchievementItem(
        id=achievement.id,
        code=achievement.code,
        name=achievement.name,
        description=achievement.description,
        icon=achievement.icon,
        rarity=achievement.rarity,
        category=achievement.category,
        exp_reward=achievement.exp_reward,
        points_reward=achievement.points_reward,
        unlocked_at=user_achievement.unlocked_at
    )


@router.get("", response_model=AchievementListResponse)
async def get_all_achievements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Achievement)
        .where(func.coalesce(Achievement.is_active, True) == True)
        .order_by(Achievement.category, Achievement.sort_order)
    )
    all_achievements = result.scalars().all()
    category_map = {}
    for a in all_achievements:
        if a.category not in category_map:
            category_map[a.category] = []
        category_map[a.category].append(AchievementInfo.model_validate(a))
    categories = []
    for cat_code in CATEGORY_ORDER:
        categories.append(AchievementCategory(
            category=cat_code,
            category_name=CATEGORY_NAMES.get(cat_code, cat_code),
            achievements=category_map.get(cat_code, [])
        ))
    return AchievementListResponse(categories=categories)


@router.get("/mine", response_model=UserAchievementResponse)
async def get_my_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_pairs = await sync_user_achievements(db, current_user, commit=True)
    result = await db.execute(
        select(UserAchievement, Achievement).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).where(
            UserAchievement.user_id == current_user.id,
            func.coalesce(Achievement.is_active, True) == True
        ).order_by(desc(UserAchievement.unlocked_at))
    )
    unlocked = [
        build_user_achievement_item(ua, a)
        for ua, a in result.all()
    ]
    newly_unlocked = [
        build_user_achievement_item(ua, a)
        for ua, a in sorted(new_pairs, key=lambda pair: pair[0].unlocked_at, reverse=True)
    ]
    total_result = await db.execute(
        select(func.count()).select_from(Achievement).where(func.coalesce(Achievement.is_active, True) == True)
    )
    total_achievements = total_result.scalar() or 0
    total_unlocked = len(unlocked)
    completion_rate = round(total_unlocked / total_achievements * 100, 1) if total_achievements > 0 else 0
    total_exp_rewarded = sum(item.exp_reward for item in unlocked)
    total_points_rewarded = sum(item.points_reward for item in unlocked)
    next_rank = get_next_rank(current_user.level or 1)
    return UserAchievementResponse(
        unlocked=unlocked,
        newly_unlocked=newly_unlocked,
        total_unlocked=total_unlocked,
        total_achievements=total_achievements,
        completion_rate=completion_rate,
        current_level=current_user.level or 1,
        current_exp=current_user.exp or 0,
        next_level_exp=next_rank["exp_required"] if next_rank else None,
        total_exp_rewarded=total_exp_rewarded,
        total_points_rewarded=total_points_rewarded
    )


@router.get("/progress", response_model=AchievementProgressResponse)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_pairs = await sync_user_achievements(db, current_user, commit=True)
    all_result = await db.execute(
        select(Achievement)
        .where(func.coalesce(Achievement.is_active, True) == True)
        .order_by(Achievement.category, Achievement.sort_order)
    )
    all_achievements = all_result.scalars().all()

    unlocked_result = await db.execute(
        select(UserAchievement.achievement_id).where(UserAchievement.user_id == current_user.id)
    )
    unlocked_ids = {r[0] for r in unlocked_result.all()}

    progress = []
    for a in all_achievements:
        current_value = await get_user_stat_value(db, current_user.id, a.condition_type)
        is_unlocked = a.id in unlocked_ids
        percentage = min(round(current_value / a.condition_value * 100, 1), 100.0) if a.condition_value > 0 else 0
        progress.append(AchievementProgressItem(
            achievement_id=a.id,
            code=a.code,
            name=a.name,
            description=a.description,
            icon=a.icon,
            rarity=a.rarity,
            category=a.category,
            condition_type=a.condition_type,
            exp_reward=a.exp_reward,
            points_reward=a.points_reward,
            current_value=current_value,
            target_value=a.condition_value,
            percentage=percentage,
            is_unlocked=is_unlocked
        ))
    newly_unlocked = [
        build_user_achievement_item(ua, a)
        for ua, a in sorted(new_pairs, key=lambda pair: pair[0].unlocked_at, reverse=True)
    ]
    return AchievementProgressResponse(progress=progress, newly_unlocked=newly_unlocked)

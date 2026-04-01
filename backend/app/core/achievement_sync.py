from typing import List, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.levels import LEARNING_MIN_DURATION_SECONDS, calculate_level
from app.models.achievement import Achievement, UserAchievement
from app.models.challenge import ChallengeSubmission
from app.models.learning import LearningRecord, PoemFavorite
from app.models.relay import RelayPlayer, RelayRoom
from app.models.social import UserFollow
from app.models.user import User
from app.models.work import Work, WorkStatus

CATEGORY_ORDER = ["growth", "learning", "creation", "social", "challenge", "relay"]
CATEGORY_NAMES = {
    "growth": "青云有阶",
    "learning": "学海无涯",
    "creation": "妙笔生花",
    "social": "高山流水",
    "challenge": "过关斩将",
    "relay": "珠联璧合"
}


async def get_user_stat_value(db: AsyncSession, user_id: int, condition_type: str) -> int:
    if condition_type == "poems_read":
        result = await db.execute(
            select(func.count(func.distinct(LearningRecord.poem_id))).select_from(LearningRecord).where(
                and_(
                    LearningRecord.user_id == user_id,
                    LearningRecord.action == "view",
                    LearningRecord.duration >= LEARNING_MIN_DURATION_SECONDS
                )
            )
        )
        return result.scalar() or 0
    if condition_type == "poems_favorited":
        result = await db.execute(
            select(func.count()).select_from(PoemFavorite).where(PoemFavorite.user_id == user_id)
        )
        return result.scalar() or 0
    if condition_type == "works_published":
        result = await db.execute(
            select(func.count()).select_from(Work).where(
                and_(Work.user_id == user_id, Work.status == WorkStatus.PUBLISHED)
            )
        )
        return result.scalar() or 0
    if condition_type == "works_liked_received":
        result = await db.execute(
            select(func.coalesce(func.sum(Work.like_count), 0)).where(Work.user_id == user_id)
        )
        return result.scalar() or 0
    if condition_type == "followers_count":
        result = await db.execute(
            select(func.count()).select_from(UserFollow).where(UserFollow.following_id == user_id)
        )
        return result.scalar() or 0
    if condition_type == "following_count":
        result = await db.execute(
            select(func.count()).select_from(UserFollow).where(UserFollow.follower_id == user_id)
        )
        return result.scalar() or 0
    if condition_type == "relay_games":
        result = await db.execute(
            select(func.count()).select_from(RelayPlayer).join(
                RelayRoom,
                RelayPlayer.room_id == RelayRoom.id
            ).where(
                and_(RelayPlayer.user_id == user_id, RelayRoom.status == "finished")
            )
        )
        return result.scalar() or 0
    if condition_type == "relay_max_combo":
        result = await db.execute(
            select(func.coalesce(func.max(RelayPlayer.max_combo), 0)).where(RelayPlayer.user_id == user_id)
        )
        return result.scalar() or 0
    if condition_type == "challenges_completed":
        result = await db.execute(
            select(func.count()).select_from(ChallengeSubmission).where(ChallengeSubmission.user_id == user_id)
        )
        return result.scalar() or 0
    if condition_type == "user_level":
        result = await db.execute(select(User.exp).where(User.id == user_id))
        return calculate_level(result.scalar() or 0)
    return 0


async def sync_user_achievements(
    db: AsyncSession,
    user: User,
    *,
    commit: bool = False
) -> List[Tuple[UserAchievement, Achievement]]:
    await db.flush()
    locked_user_result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = locked_user_result.scalar_one()
    user = locked_user
    current_exp = user.exp or 0
    normalized_level = calculate_level(current_exp)
    level_changed = user.level != normalized_level
    if level_changed:
        user.level = normalized_level

    all_result = await db.execute(
        select(Achievement)
        .where(func.coalesce(Achievement.is_active, True) == True)
        .order_by(Achievement.category, Achievement.sort_order, Achievement.id)
    )
    all_achievements = all_result.scalars().all()

    unlocked_result = await db.execute(
        select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)
    )
    unlocked_ids = set(unlocked_result.scalars().all())

    new_pairs: List[Tuple[UserAchievement, Achievement]] = []
    total_exp_reward = 0
    total_points_reward = 0

    while True:
        unlocked_in_pass = False
        for achievement in all_achievements:
            if achievement.id in unlocked_ids:
                continue
            if achievement.condition_type == "user_level":
                current_value = calculate_level(current_exp + total_exp_reward)
            else:
                current_value = await get_user_stat_value(db, user.id, achievement.condition_type)
            if current_value < achievement.condition_value:
                continue
            insert_result = await db.execute(
                pg_insert(UserAchievement)
                .values(user_id=user.id, achievement_id=achievement.id)
                .on_conflict_do_nothing(index_elements=["user_id", "achievement_id"])
                .returning(UserAchievement.id, UserAchievement.unlocked_at)
            )
            inserted = insert_result.first()
            if not inserted:
                continue
            unlocked = UserAchievement(
                id=inserted.id,
                user_id=user.id,
                achievement_id=achievement.id,
                unlocked_at=inserted.unlocked_at
            )
            unlocked_ids.add(achievement.id)
            total_exp_reward += achievement.exp_reward or 0
            total_points_reward += achievement.points_reward or 0
            new_pairs.append((unlocked, achievement))
            unlocked_in_pass = True
        if not unlocked_in_pass:
            break

    if new_pairs:
        user.exp = current_exp + total_exp_reward
        user.points = (user.points or 0) + total_points_reward
        user.level = calculate_level(user.exp or 0)

    if commit:
        if level_changed or new_pairs:
            await db.commit()
    elif level_changed or new_pairs:
        await db.flush()

    return new_pairs

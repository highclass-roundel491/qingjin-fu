from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
from typing import Optional
from app.core.database import get_db
from app.core.achievement_sync import sync_user_achievements
from app.models.social import UserFollow, ActivityFeed
from app.models.user import User
from app.models.work import Work
from app.models.achievement import Achievement, UserAchievement
from app.schemas.social import (
    FollowResponse, FollowingItem, FollowingListResponse,
    FollowerItem, FollowerListResponse, UserPublicProfile,
    UserAchievementBrief, RecentWorkBrief,
    ActivityFeedItem, ActivityFeedResponse
)
from app.api.deps import get_current_user, get_current_user_optional
from app.core.levels import calculate_level

router = APIRouter()


@router.post("/follow/{user_id}", response_model=FollowResponse)
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    target_result = await db.execute(select(User).where(User.id == user_id))
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    existing = await db.execute(
        select(UserFollow).where(and_(UserFollow.follower_id == current_user.id, UserFollow.following_id == user_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已经关注该用户")
    follow = UserFollow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    mutual_result = await db.execute(
        select(UserFollow).where(and_(UserFollow.follower_id == user_id, UserFollow.following_id == current_user.id))
    )
    is_mutual = mutual_result.scalar_one_or_none() is not None
    await sync_user_achievements(db, current_user)
    await sync_user_achievements(db, target)
    await db.commit()
    return FollowResponse(following_id=user_id, following_username=target.username, is_mutual=is_mutual)


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserFollow).where(and_(UserFollow.follower_id == current_user.id, UserFollow.following_id == user_id))
    )
    follow = result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=404, detail="未关注该用户")
    await db.delete(follow)
    await db.commit()
    return {"code": 200, "message": "取消关注成功"}


@router.get("/following", response_model=FollowingListResponse)
async def get_following(
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    target_id = user_id or current_user.id
    query = select(UserFollow, User).join(User, UserFollow.following_id == User.id).where(
        UserFollow.follower_id == target_id
    ).order_by(desc(UserFollow.created_at))
    count_q = select(func.count()).select_from(
        select(UserFollow).where(UserFollow.follower_id == target_id).subquery()
    )
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = []
    for follow, u in result.all():
        mutual_result = await db.execute(
            select(UserFollow).where(and_(UserFollow.follower_id == u.id, UserFollow.following_id == target_id))
        )
        is_mutual = mutual_result.scalar_one_or_none() is not None
        items.append(FollowingItem(
            user_id=u.id, username=u.username, nickname=u.nickname,
            avatar_url=u.avatar_url, bio=u.bio, level=calculate_level(u.exp or 0),
            is_mutual=is_mutual, followed_at=follow.created_at
        ))
    return FollowingListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/followers", response_model=FollowerListResponse)
async def get_followers(
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    target_id = user_id or current_user.id
    query = select(UserFollow, User).join(User, UserFollow.follower_id == User.id).where(
        UserFollow.following_id == target_id
    ).order_by(desc(UserFollow.created_at))
    count_q = select(func.count()).select_from(
        select(UserFollow).where(UserFollow.following_id == target_id).subquery()
    )
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = []
    for follow, u in result.all():
        following_result = await db.execute(
            select(UserFollow).where(and_(UserFollow.follower_id == current_user.id, UserFollow.following_id == u.id))
        )
        is_following = following_result.scalar_one_or_none() is not None
        items.append(FollowerItem(
            user_id=u.id, username=u.username, nickname=u.nickname,
            avatar_url=u.avatar_url, bio=u.bio, level=calculate_level(u.exp or 0),
            is_following=is_following, followed_at=follow.created_at
        ))
    return FollowerListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/users/{user_id}/profile", response_model=UserPublicProfile)
async def get_user_profile(
    user_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    async def q_following_count():
        r = await db.execute(select(func.count()).select_from(UserFollow).where(UserFollow.follower_id == user_id))
        return r.scalar() or 0

    async def q_follower_count():
        r = await db.execute(select(func.count()).select_from(UserFollow).where(UserFollow.following_id == user_id))
        return r.scalar() or 0

    async def q_work_count():
        r = await db.execute(select(func.count()).select_from(Work).where(and_(Work.user_id == user_id, Work.status == "published")))
        return r.scalar() or 0

    async def q_follow_status():
        if not current_user or current_user.id == user_id:
            return False, False
        f1 = await db.execute(select(UserFollow).where(and_(UserFollow.follower_id == current_user.id, UserFollow.following_id == user_id)))
        f2 = await db.execute(select(UserFollow).where(and_(UserFollow.follower_id == user_id, UserFollow.following_id == current_user.id)))
        return f1.scalar_one_or_none() is not None, f2.scalar_one_or_none() is not None

    async def q_achievements():
        r = await db.execute(
            select(UserAchievement, Achievement).join(Achievement, UserAchievement.achievement_id == Achievement.id).where(
                UserAchievement.user_id == user_id,
                func.coalesce(Achievement.is_active, True) == True
            ).order_by(desc(UserAchievement.unlocked_at)).limit(6)
        )
        return [
            UserAchievementBrief(id=a.id, code=a.code, name=a.name, description=a.description, icon=a.icon, rarity=a.rarity, unlocked_at=ua.unlocked_at)
            for ua, a in r.all()
        ]

    async def q_recent_works():
        r = await db.execute(
            select(Work).where(and_(Work.user_id == user_id, Work.status == "published")).order_by(desc(Work.published_at)).limit(5)
        )
        return [
            RecentWorkBrief(id=w.id, title=w.title, genre=w.genre, like_count=w.like_count, published_at=w.published_at)
            for w in r.scalars().all()
        ]

    import asyncio
    following_count, follower_count, work_count, (is_following, is_follower), achievements, recent_works = await asyncio.gather(
        q_following_count(), q_follower_count(), q_work_count(), q_follow_status(), q_achievements(), q_recent_works()
    )

    return UserPublicProfile(
        user_id=user.id, username=user.username, nickname=user.nickname,
        avatar_url=user.avatar_url, bio=user.bio, level=calculate_level(user.exp or 0), exp=user.exp or 0,
        following_count=following_count, follower_count=follower_count,
        work_count=work_count, is_following=is_following, is_follower=is_follower,
        achievements=achievements, recent_works=recent_works, joined_at=user.created_at
    )


@router.get("/feed", response_model=ActivityFeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    following_ids_q = select(UserFollow.following_id).where(UserFollow.follower_id == current_user.id)
    following_result = await db.execute(following_ids_q)
    following_ids = [r[0] for r in following_result.all()]
    following_ids.append(current_user.id)

    query = select(ActivityFeed, User).join(User, ActivityFeed.user_id == User.id).where(
        ActivityFeed.user_id.in_(following_ids)
    ).order_by(desc(ActivityFeed.created_at))

    count_q = select(func.count()).select_from(
        select(ActivityFeed).where(ActivityFeed.user_id.in_(following_ids)).subquery()
    )
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = [
        ActivityFeedItem(
            id=af.id, type=af.type, user_id=af.user_id, username=u.username,
            avatar_url=u.avatar_url, content=af.content,
            reference_id=af.reference_id, reference_type=af.reference_type,
            created_at=af.created_at
        )
        for af, u in result.all()
    ]
    return ActivityFeedResponse(items=items, total=total, page=page, page_size=page_size)

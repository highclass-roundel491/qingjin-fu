from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, union_all, literal, cast, String, Integer, text
from datetime import timedelta
from typing import List
import os
import uuid
import re
from ....core.database import get_db
from ....core.config import settings
from ....core.achievement_sync import sync_user_achievements
from ....core.security import get_password_hash, verify_password, create_access_token
from ....models.user import User
from ....models.poem import Poem
from ....models.learning import LearningRecord, PoemFavorite, UserStats
from ....models.challenge import DailyChallenge, ChallengeSubmission
from ....models.feihualing import FeiHuaLingGame, FeiHuaLingRound
from ....models.relay import RelayPlayer, RelayRoom
from ....models.achievement import Achievement, UserAchievement
from ....models.work import Work
from ....schemas.poem import PoemListItem, PoemListResponse
from ....schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    UserUpdate,
    ChangePasswordRequest,
    UserExpHistoryItem,
    UserExpHistoryResponse,
    UserProfileStats
)
from ....api.deps import get_current_user
from ....core.levels import (
    LEARNING_MIN_DURATION_SECONDS,
    LEARNING_EXP_PER_POEM,
    RELAY_EXP_RATE,
    calculate_feihualing_exp,
    calculate_feihualing_score,
    calculate_learning_exp,
    calculate_level,
    calculate_relay_rewards,
)

router = APIRouter()

def serialize_user_response(user: User) -> UserResponse:
    exp = user.exp or 0
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        bio=user.bio,
        level=calculate_level(exp),
        exp=exp,
        points=user.points or 0,
        created_at=user.created_at
    )

async def build_favorites_payload(user_id: int, page: int, page_size: int, db: AsyncSession) -> PoemListResponse:
    query = select(Poem).join(PoemFavorite).where(
        PoemFavorite.user_id == user_id
    ).order_by(PoemFavorite.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    poems = result.scalars().all()

    items = []
    for poem in poems:
        items.append(PoemListItem(
            id=poem.id,
            title=poem.title,
            author=poem.author,
            dynasty=poem.dynasty,
            content=poem.content,
            category=poem.category,
            genre=poem.genre,
            view_count=poem.view_count or 0,
            favorite_count=poem.favorite_count or 0
        ))

    return PoemListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

async def build_user_stats_payload(user_id: int, db: AsyncSession) -> UserProfileStats:
    stats_result = await db.execute(select(UserStats).where(UserStats.user_id == user_id))
    user_stats = stats_result.scalar_one_or_none()

    challenge_total_result = await db.execute(
        select(func.count()).select_from(ChallengeSubmission).where(ChallengeSubmission.user_id == user_id)
    )
    challenge_total = challenge_total_result.scalar() or 0

    challenge_success_result = await db.execute(
        select(func.count()).select_from(ChallengeSubmission).where(
            ChallengeSubmission.user_id == user_id,
            ChallengeSubmission.ai_score >= 80
        )
    )
    challenge_success = challenge_success_result.scalar() or 0

    works_total_result = await db.execute(
        select(func.count()).select_from(Work).where(Work.user_id == user_id)
    )
    works_total = works_total_result.scalar() or 0

    likes_total_result = await db.execute(
        select(func.coalesce(func.sum(Work.like_count), 0)).where(Work.user_id == user_id)
    )
    likes_total = likes_total_result.scalar() or 0

    correct_rate = round((challenge_success / challenge_total) * 100, 1) if challenge_total else 0.0

    return UserProfileStats(
        total_study_time=user_stats.study_time if user_stats else 0,
        total_poems_learned=user_stats.total_learned if user_stats else 0,
        total_questions_answered=challenge_total,
        correct_rate=correct_rate,
        total_works_created=works_total,
        total_likes_received=likes_total,
        follower_count=0,
        following_count=0
    )


def shorten_text(text: str, limit: int = 18) -> str:
    normalized = " ".join((text or "").split())
    if not normalized:
        return "未命名记录"
    return normalized if len(normalized) <= limit else f"{normalized[:limit]}…"


async def build_user_exp_history_payload(user_id: int, page: int, page_size: int, db: AsyncSession) -> UserExpHistoryResponse:
    q_challenge = (
        select(
            (literal("challenge-") + cast(ChallengeSubmission.id, String)).label("row_id"),
            literal("challenge").label("source"),
            literal("妙笔挑战").label("source_label"),
            DailyChallenge.challenge_type.label("sub_type"),
            func.coalesce(
                ChallengeSubmission.content,
                func.concat(
                    func.coalesce(ChallengeSubmission.answer, literal("")),
                    literal(" / "),
                    func.coalesce(ChallengeSubmission.answer_2, literal("")),
                ),
            ).label("raw_detail"),
            ChallengeSubmission.exp_gained.label("exp"),
            ChallengeSubmission.submitted_at.label("occurred_at"),
            literal(0).label("extra_int"),
        )
        .join(DailyChallenge, DailyChallenge.id == ChallengeSubmission.challenge_id)
        .where(ChallengeSubmission.user_id == user_id, ChallengeSubmission.exp_gained > 0)
    )

    first_learning = (
        select(
            LearningRecord.id,
            LearningRecord.poem_id,
            LearningRecord.created_at,
            func.row_number()
            .over(partition_by=LearningRecord.poem_id, order_by=[LearningRecord.created_at.asc(), LearningRecord.id.asc()])
            .label("rn"),
        )
        .where(
            LearningRecord.user_id == user_id,
            LearningRecord.action == "view",
            LearningRecord.duration >= LEARNING_MIN_DURATION_SECONDS,
        )
        .subquery("first_lr")
    )
    q_learning = (
        select(
            (literal("learning-") + cast(first_learning.c.id, String)).label("row_id"),
            literal("learning").label("source"),
            literal("诗词研习").label("source_label"),
            literal("view").label("sub_type"),
            Poem.title.label("raw_detail"),
            literal(LEARNING_EXP_PER_POEM).label("exp"),
            first_learning.c.created_at.label("occurred_at"),
            literal(0).label("extra_int"),
        )
        .select_from(first_learning)
        .join(Poem, Poem.id == first_learning.c.poem_id)
        .where(first_learning.c.rn == 1)
    )

    q_works = (
        select(
            (literal("work-") + cast(Work.id, String)).label("row_id"),
            literal("work").label("source"),
            literal("作品创作").label("source_label"),
            literal("publish").label("sub_type"),
            Work.title.label("raw_detail"),
            Work.exp_awarded.label("exp"),
            func.coalesce(Work.published_at, Work.updated_at, Work.created_at).label("occurred_at"),
            literal(0).label("extra_int"),
        )
        .where(Work.user_id == user_id, Work.status == "published", Work.exp_awarded > 0)
    )

    q_achievement = (
        select(
            (literal("achievement-") + cast(UserAchievement.id, String)).label("row_id"),
            literal("achievement").label("source"),
            literal("成就解锁").label("source_label"),
            literal("unlock").label("sub_type"),
            Achievement.name.label("raw_detail"),
            Achievement.exp_reward.label("exp"),
            UserAchievement.unlocked_at.label("occurred_at"),
            literal(0).label("extra_int"),
        )
        .join(Achievement, Achievement.id == UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user_id, Achievement.exp_reward > 0)
    )

    q_relay = (
        select(
            (literal("relay-") + cast(RelayRoom.id, String) + literal("-") + cast(RelayPlayer.id, String)).label("row_id"),
            literal("relay").label("source"),
            literal("诗词接龙").label("source_label"),
            RelayRoom.mode.label("sub_type"),
            cast(func.coalesce(RelayPlayer.score, 0), String).label("raw_detail"),
            cast(func.greatest(func.floor(func.coalesce(RelayPlayer.score, 0) * RELAY_EXP_RATE), 0), Integer).label("exp"),
            func.coalesce(RelayRoom.finished_at, RelayRoom.created_at).label("occurred_at"),
            func.coalesce(RelayPlayer.score, 0).label("extra_int"),
        )
        .join(RelayPlayer, RelayPlayer.room_id == RelayRoom.id)
        .where(RelayPlayer.user_id == user_id, RelayRoom.status == "finished")
    )

    combined = union_all(q_challenge, q_learning, q_works, q_achievement, q_relay).subquery("combined")

    filtered = select(combined).where(combined.c.exp > 0).subquery("filtered")

    count_result = await db.execute(select(func.count()).select_from(filtered))
    sql_total = count_result.scalar() or 0

    page_q = (
        select(filtered)
        .order_by(filtered.c.occurred_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(page_q)).all()

    fhl_result = await db.execute(
        select(
            FeiHuaLingGame.id,
            FeiHuaLingGame.keyword,
            FeiHuaLingGame.total_rounds,
            func.coalesce(FeiHuaLingGame.ended_at, FeiHuaLingGame.created_at).label("occurred_at"),
        )
        .where(
            FeiHuaLingGame.user_id == user_id,
            FeiHuaLingGame.status == "finished",
            FeiHuaLingGame.total_rounds.in_([5, 10, 15]),
        )
    )
    fhl_games = fhl_result.all()
    fhl_items: List[UserExpHistoryItem] = []
    if fhl_games:
        game_ids = [g.id for g in fhl_games]
        rounds_result = await db.execute(
            select(
                FeiHuaLingRound.game_id,
                FeiHuaLingRound.round_number,
                FeiHuaLingRound.response_time,
            )
            .where(FeiHuaLingRound.game_id.in_(game_ids), FeiHuaLingRound.player == "user")
            .order_by(FeiHuaLingRound.game_id, FeiHuaLingRound.round_number)
        )
        rounds_by_game = {}
        for r in rounds_result.all():
            rounds_by_game.setdefault(r.game_id, []).append(r)

        game_map = {g.id: g for g in fhl_games}
        for gid, rounds in rounds_by_game.items():
            game = game_map[gid]
            exp_gained = sum(
                calculate_feihualing_exp(
                    calculate_feihualing_score(game.total_rounds or 10, r.response_time or 30, r.round_number or 1)
                )
                for r in rounds
            )
            if exp_gained <= 0:
                continue
            fhl_items.append(UserExpHistoryItem(
                id=f"feihualing-{gid}",
                source="feihualing",
                source_label="飞花令",
                title="飞花令闯关",
                detail=f"完成「{game.keyword}」主题 {len(rounds)} 轮闯关",
                exp=exp_gained,
                occurred_at=game.occurred_at,
            ))

    fhl_total = len(fhl_items)
    total = sql_total + fhl_total

    _TITLE_MAP = {
        "challenge": lambda st: "续写接力" if st == "continue_line" else "填字妙想",
        "learning": lambda _: "首次有效研习",
        "work": lambda _: "作品发布",
        "achievement": lambda _: "成就奖励",
        "relay": lambda _: "接龙结算",
    }
    _DETAIL_MAP = {
        "challenge": lambda st, d: f"完成{'续写接力' if st == 'continue_line' else '填字妙想'}，内容「{shorten_text(d, 20)}」",
        "learning": lambda _, d: f"研习《{shorten_text(d, 16)}》",
        "work": lambda _, d: f"发布《{shorten_text(d, 16)}》",
        "achievement": lambda _, d: f"解锁「{d}」",
        "relay": lambda st, d: f"{'多人对弈' if st == 'multi' else '单人闯关'}得分 {d}",
    }

    sql_items = []
    for r in rows:
        src = r.source
        sql_items.append(UserExpHistoryItem(
            id=r.row_id,
            source=src,
            source_label=r.source_label,
            title=_TITLE_MAP[src](r.sub_type),
            detail=_DETAIL_MAP[src](r.sub_type, r.raw_detail),
            exp=r.exp,
            occurred_at=r.occurred_at,
        ))

    if not fhl_items:
        items = sql_items
    else:
        merged = sql_items + fhl_items
        merged.sort(key=lambda x: x.occurred_at, reverse=True)
        items = merged[:page_size]

    return UserExpHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=await get_password_hash(user_data.password)
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "code": 201,
        "message": "注册成功",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@router.post("/login", response_model=dict)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not await verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=7)
    )
    
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    }

@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await sync_user_achievements(db, current_user, commit=True)
    return {
        "code": 200,
        "message": "success",
        "data": serialize_user_response(current_user)
    }

@router.put("/me", response_model=dict)
async def update_current_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="请至少提供一个需要更新的字段")

    if "email" in update_data:
        new_email = (update_data["email"] or "").strip()
        if new_email:
            if not re.match(r'^[\w.+-]+@[\w-]+\.[\w.]+$', new_email):
                raise HTTPException(status_code=400, detail="邮箱格式不正确")
            existing = await db.execute(
                select(User).where(and_(User.email == new_email, User.id != current_user.id))
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
            current_user.email = new_email

    if "phone" in update_data:
        new_phone = (update_data["phone"] or "").strip() or None
        if new_phone:
            if not re.match(r'^1[3-9]\d{9}$', new_phone):
                raise HTTPException(status_code=400, detail="手机号格式不正确")
            existing = await db.execute(
                select(User).where(and_(User.phone == new_phone, User.id != current_user.id))
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="该手机号已被其他用户使用")
        current_user.phone = new_phone

    if "nickname" in update_data:
        current_user.nickname = (update_data["nickname"] or "").strip() or None
    if "avatar_url" in update_data:
        current_user.avatar_url = (update_data["avatar_url"] or "").strip() or None
    if "bio" in update_data:
        current_user.bio = (update_data["bio"] or "").strip() or None

    await db.commit()
    await db.refresh(current_user)

    return {
        "code": 200,
        "message": "用户信息更新成功",
        "data": serialize_user_response(current_user)
    }


@router.post("/me/avatar", response_model=dict)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_AVATAR_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"仅支持 {', '.join(settings.ALLOWED_AVATAR_EXTENSIONS)} 格式")

    content = await file.read()
    if len(content) > settings.MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="头像文件不能超过 2MB")

    avatar_dir = os.path.join(settings.UPLOAD_DIR, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(avatar_dir, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(current_user)

    return {
        "code": 200,
        "message": "头像上传成功",
        "data": {"avatar_url": avatar_url}
    }

@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not await verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    if password_data.old_password == password_data.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")

    current_user.password_hash = await get_password_hash(password_data.new_password)
    await db.commit()

    return {
        "code": 200,
        "message": "密码修改成功"
    }

@router.get("/me/favorites", response_model=dict)
async def get_current_user_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await build_favorites_payload(current_user.id, page, page_size, db)

    return {
        "code": 200,
        "message": "success",
        "data": data.model_dump()
    }


@router.get("/me/exp-history", response_model=dict)
async def get_current_user_exp_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await build_user_exp_history_payload(current_user.id, page, page_size, db)

    return {
        "code": 200,
        "message": "success",
        "data": data.model_dump()
    }

@router.get("/{user_id}/stats", response_model=dict)
async def get_user_profile_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    data = await build_user_stats_payload(user_id, db)

    return {
        "code": 200,
        "message": "success",
        "data": data.model_dump()
    }

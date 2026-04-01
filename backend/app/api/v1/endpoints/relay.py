from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timezone, timedelta
from typing import Optional
import random
import string
from app.core.database import get_db
from app.core.achievement_sync import sync_user_achievements
from app.models.relay import RelayRoom, RelayPlayer, RelayRound
from app.models.poem import Poem
from app.models.user import User
from app.schemas.relay import (
    RelayRoomCreateRequest, RelayRoomResponse, RelayRoomDetailResponse,
    RelayStartResponse, RelaySubmitRequest, RelaySubmitResponse,
    RelayHintResponse, RelayHintItem, RelayEndResponse, RelayEndResultItem,
    RelayHistoryResponse, RelayHistoryItem, RelayRankingResponse, RelayRankingItem,
    RelayPlayerInfo, RelayRoundInfo, RelayLobbyResponse, RelayLobbyItem
)
from app.api.deps import get_current_user
from app.core.levels import calculate_level, calculate_relay_rewards

router = APIRouter()


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def get_last_char(verse):
    clean = verse.rstrip('\u3002\uff0c\uff01\uff1f\u3001\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09')
    return clean[-1] if clean else verse[-1]


async def get_random_starter_verse(db):
    count_result = await db.execute(select(func.count()).select_from(Poem))
    total = count_result.scalar() or 0
    if total == 0:
        return {"verse": "\u5e8a\u524d\u660e\u6708\u5149", "poem_title": "\u9759\u591c\u601d", "author": "\u674e\u767d"}
    offset = random.randint(0, max(0, total - 1))
    result = await db.execute(select(Poem).offset(offset).limit(1))
    poem = result.scalar_one_or_none()
    if not poem:
        return {"verse": "\u5e8a\u524d\u660e\u6708\u5149", "poem_title": "\u9759\u591c\u601d", "author": "\u674e\u767d"}
    lines = [l.strip() for l in poem.content.replace('\r\n', '\n').split('\n') if l.strip()]
    if not lines:
        lines = [poem.content[:20]]
    verse = random.choice(lines)
    if '\uff0c' in verse:
        verse = verse.split('\uff0c')[0]
    elif '\u3002' in verse:
        verse = verse.split('\u3002')[0]
    return {"verse": verse, "poem_title": poem.title, "author": poem.author}


async def find_matching_verses(db, char, limit=20):
    result = await db.execute(select(Poem).where(Poem.content.contains(char)).limit(limit))
    poems = result.scalars().all()
    matches = []
    for poem in poems:
        lines = [l.strip() for l in poem.content.replace('\r\n', '\n').split('\n') if l.strip()]
        for line in lines:
            for seg in line.replace('\u3002', '\uff0c').split('\uff0c'):
                seg = seg.strip()
                if seg and seg[0] == char:
                    matches.append({"verse": seg, "poem_title": poem.title, "author": poem.author})
    return matches


async def validate_verse(db, verse, expected_char, difficulty):
    first_char = verse[0] if verse else ""
    if first_char != expected_char:
        return {"is_valid": False, "match_type": "none", "poem_title": None, "author": None}
    result = await db.execute(select(Poem).where(Poem.content.contains(verse)).limit(1))
    poem = result.scalar_one_or_none()
    if poem:
        return {"is_valid": True, "match_type": "exact", "poem_title": poem.title, "author": poem.author}
    return {"is_valid": True, "match_type": "exact", "poem_title": None, "author": None}


@router.post("/rooms", response_model=RelayRoomResponse, status_code=201)
async def create_room(
    req: RelayRoomCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pwd = req.password.strip() if req.password else None
    room = RelayRoom(
        room_code=generate_room_code(), host_id=current_user.id,
        mode=req.mode, difficulty=req.difficulty,
        max_rounds=req.max_rounds, time_limit=req.time_limit,
        max_players=req.max_players, status="waiting",
        password=pwd
    )
    db.add(room)
    await db.flush()
    player = RelayPlayer(room_id=room.id, user_id=current_user.id, is_host=True)
    db.add(player)
    await db.commit()
    await db.refresh(room)
    return RelayRoomResponse(
        id=room.id, room_code=room.room_code, mode=room.mode,
        difficulty=room.difficulty, max_rounds=room.max_rounds,
        time_limit=room.time_limit, status=room.status,
        host_id=room.host_id, host_username=current_user.username,
        created_at=room.created_at, max_players=room.max_players or 2,
        has_password=bool(pwd)
    )


@router.get("/lobby", response_model=RelayLobbyResponse)
async def get_lobby(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    stale_rooms = await db.execute(
        select(RelayRoom).where(
            and_(RelayRoom.status == "waiting", RelayRoom.created_at < cutoff)
        )
    )
    for stale in stale_rooms.scalars().all():
        stale.status = "finished"
    await db.flush()

    base_q = select(RelayRoom).where(
        and_(RelayRoom.status == "waiting", RelayRoom.mode == "multi")
    ).order_by(desc(RelayRoom.created_at))
    count_q = select(func.count()).select_from(base_q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    result = await db.execute(base_q.offset((page - 1) * page_size).limit(page_size))
    items = []
    for room in result.scalars().all():
        host_result = await db.execute(select(User).where(User.id == room.host_id))
        host = host_result.scalar_one_or_none()
        player_count_result = await db.execute(
            select(func.count()).select_from(RelayPlayer).where(RelayPlayer.room_id == room.id)
        )
        player_count = player_count_result.scalar() or 0
        items.append(RelayLobbyItem(
            id=room.id, room_code=room.room_code,
            difficulty=room.difficulty, max_rounds=room.max_rounds,
            time_limit=room.time_limit, max_players=room.max_players or 2,
            player_count=player_count,
            host_username=host.username if host else "",
            host_avatar=host.avatar_url if host else None,
            has_password=bool(room.password),
            created_at=room.created_at
        ))
    return RelayLobbyResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/quick-match", response_model=RelayRoomResponse)
async def quick_match(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RelayRoom).where(
            and_(RelayRoom.status == "waiting", RelayRoom.mode == "multi",
                 RelayRoom.password.is_(None))
        ).order_by(RelayRoom.created_at).limit(10)
    )
    rooms = result.scalars().all()
    for room in rooms:
        player_count_result = await db.execute(
            select(func.count()).select_from(RelayPlayer).where(RelayPlayer.room_id == room.id)
        )
        count = player_count_result.scalar() or 0
        if count < (room.max_players or 2):
            existing = await db.execute(
                select(RelayPlayer).where(
                    and_(RelayPlayer.room_id == room.id, RelayPlayer.user_id == current_user.id)
                )
            )
            if not existing.scalar_one_or_none():
                player = RelayPlayer(room_id=room.id, user_id=current_user.id, is_host=False)
                db.add(player)
                await db.commit()
            host_result = await db.execute(select(User).where(User.id == room.host_id))
            host = host_result.scalar_one_or_none()
            return RelayRoomResponse(
                id=room.id, room_code=room.room_code, mode=room.mode,
                difficulty=room.difficulty, max_rounds=room.max_rounds,
                time_limit=room.time_limit, status=room.status,
                host_id=room.host_id,
                host_username=host.username if host else "",
                created_at=room.created_at, max_players=room.max_players or 2
            )
    room = RelayRoom(
        room_code=generate_room_code(), host_id=current_user.id,
        mode="multi", difficulty="normal",
        max_rounds=20, time_limit=30,
        max_players=2, status="waiting"
    )
    db.add(room)
    await db.flush()
    player = RelayPlayer(room_id=room.id, user_id=current_user.id, is_host=True)
    db.add(player)
    await db.commit()
    await db.refresh(room)
    return RelayRoomResponse(
        id=room.id, room_code=room.room_code, mode=room.mode,
        difficulty=room.difficulty, max_rounds=room.max_rounds,
        time_limit=room.time_limit, status=room.status,
        host_id=room.host_id, host_username=current_user.username,
        created_at=room.created_at, max_players=room.max_players or 2
    )


@router.post("/rooms/{room_code}/join")
async def join_room(room_code: str, password: Optional[str] = Query(None), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RelayRoom).where(RelayRoom.room_code == room_code))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="游戏已开始或已结束")
    if room.password and room.password != (password or ""):
        raise HTTPException(status_code=403, detail="房间密码错误")
    existing = await db.execute(select(RelayPlayer).where(and_(RelayPlayer.room_id == room.id, RelayPlayer.user_id == current_user.id)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已在房间中")
    player = RelayPlayer(room_id=room.id, user_id=current_user.id, is_host=False)
    db.add(player)
    await db.commit()
    players_result = await db.execute(select(RelayPlayer, User).join(User, RelayPlayer.user_id == User.id).where(RelayPlayer.room_id == room.id))
    players = [{"user_id": u.id, "username": u.username, "avatar_url": u.avatar_url, "is_host": rp.is_host} for rp, u in players_result.all()]
    return {"code": 200, "message": "加入成功", "data": {"room_id": room.id, "room_code": room.room_code, "players": players}}


@router.post("/rooms/{room_id}/start", response_model=RelayStartResponse)
async def start_game(room_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有房主可以开始游戏")
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="游戏已开始或已结束")
    starter = await get_random_starter_verse(db)
    next_char = get_last_char(starter["verse"])
    room.status = "playing"
    room.current_round = 1
    room.next_char = next_char
    room.started_at = datetime.now(timezone.utc)
    first_round = RelayRound(room_id=room.id, round_number=1, user_id=0, verse=starter["verse"], poem_title=starter["poem_title"], author=starter["author"], match_type="starter", score=0, time_used=0)
    db.add(first_round)
    await db.commit()
    return RelayStartResponse(room_id=room.id, status="playing", current_round=1, starter_verse=starter["verse"], starter_poem_title=starter["poem_title"], starter_author=starter["author"], next_char=next_char, started_at=room.started_at)


@router.post("/rooms/{room_id}/submit", response_model=RelaySubmitResponse)
async def submit_verse(room_id: int, req: RelaySubmitRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.status != "playing":
        raise HTTPException(status_code=400, detail="游戏未在进行中")
    player_result = await db.execute(select(RelayPlayer).where(and_(RelayPlayer.room_id == room.id, RelayPlayer.user_id == current_user.id)))
    player = player_result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=403, detail="你不在该房间中")
    verse = req.verse.strip()
    if not verse:
        raise HTTPException(status_code=400, detail="诗句不能为空")
    validation = await validate_verse(db, verse, room.next_char, room.difficulty)
    if not validation["is_valid"]:
        player.combo = 0
        await db.commit()
        raise HTTPException(status_code=400, detail=f"诗句首字与要求的「{room.next_char}」不匹配")
    player.combo += 1
    if player.combo > player.max_combo:
        player.max_combo = player.combo
    base_score = 10
    combo_bonus = min(player.combo - 1, 5) * 2
    score = base_score + combo_bonus
    player.score += score
    player.rounds_played += 1
    next_char = get_last_char(verse)
    room.current_round += 1
    room.next_char = next_char
    new_round = RelayRound(room_id=room.id, round_number=room.current_round, user_id=current_user.id, verse=verse, poem_title=validation.get("poem_title"), author=validation.get("author"), match_type=validation["match_type"], score=score, time_used=0)
    db.add(new_round)
    if room.current_round >= room.max_rounds:
        room.status = "finished"
        room.finished_at = datetime.now(timezone.utc)
    await db.commit()
    return RelaySubmitResponse(round=room.current_round, verse=verse, poem_title=validation.get("poem_title"), author=validation.get("author"), is_valid=True, match_type=validation["match_type"], score=score, next_char=next_char, time_used=0, combo=player.combo)


@router.get("/rooms/{room_id}", response_model=RelayRoomDetailResponse)
async def get_room_detail(room_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    players_result = await db.execute(select(RelayPlayer, User).join(User, RelayPlayer.user_id == User.id).where(RelayPlayer.room_id == room.id))
    players = [RelayPlayerInfo(user_id=u.id, username=u.username, avatar_url=u.avatar_url, score=rp.score, combo=rp.combo, is_host=rp.is_host) for rp, u in players_result.all()]
    rounds_result = await db.execute(select(RelayRound).where(RelayRound.room_id == room.id).order_by(RelayRound.round_number))
    rounds_list = []
    for rr in rounds_result.scalars().all():
        username = "系统"
        if rr.user_id > 0:
            u_result = await db.execute(select(User).where(User.id == rr.user_id))
            u = u_result.scalar_one_or_none()
            if u:
                username = u.username
        rounds_list.append(RelayRoundInfo(round=rr.round_number, user_id=rr.user_id, username=username, verse=rr.verse, poem_title=rr.poem_title, author=rr.author, score=rr.score, time_used=rr.time_used))
    return RelayRoomDetailResponse(id=room.id, room_code=room.room_code, mode=room.mode, difficulty=room.difficulty, status=room.status, current_round=room.current_round, max_rounds=room.max_rounds, time_limit=room.time_limit, next_char=room.next_char, players=players, rounds=rounds_list)


@router.get("/rooms/{room_id}/hint", response_model=RelayHintResponse)
async def get_hint(room_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.status != "playing":
        raise HTTPException(status_code=400, detail="游戏未在进行中")
    player_result = await db.execute(select(RelayPlayer).where(and_(RelayPlayer.room_id == room.id, RelayPlayer.user_id == current_user.id)))
    player = player_result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=403, detail="你不在该房间中")
    if player.hints_used >= 3:
        raise HTTPException(status_code=400, detail="提示次数已用完")
    matches = await find_matching_verses(db, room.next_char, limit=20)
    random.shuffle(matches)
    hints = [RelayHintItem(verse=m["verse"], poem_title=m["poem_title"], author=m["author"]) for m in matches[:3]]
    if not hints:
        hints.append(RelayHintItem(verse=f"{room.next_char}...", poem_title="暂无匹配", author="未知"))
    player.hints_used += 1
    await db.commit()
    return RelayHintResponse(hints=hints, hint_count_used=player.hints_used, hint_count_max=3)


@router.post("/rooms/{room_id}/end", response_model=RelayEndResponse)
async def end_game(room_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room.status == "finished":
        raise HTTPException(status_code=400, detail="游戏已结束")
    room.status = "finished"
    room.finished_at = datetime.now(timezone.utc)
    duration = int((room.finished_at - room.started_at).total_seconds()) if room.started_at else 0
    players_result = await db.execute(select(RelayPlayer, User).join(User, RelayPlayer.user_id == User.id).where(RelayPlayer.room_id == room.id).order_by(desc(RelayPlayer.score)))
    results = []
    rank = 1
    my_exp_gained = 0
    my_points_gained = 0
    all_new_achievements = []
    for rp, u in players_result.all():
        avg_time = rp.total_time / rp.rounds_played if rp.rounds_played > 0 else 0
        rewards = calculate_relay_rewards(rp.score)
        u.exp = (u.exp or 0) + rewards["exp"]
        u.points = (u.points or 0) + rewards["points"]
        u.level = calculate_level(u.exp)
        results.append(RelayEndResultItem(user_id=u.id, username=u.username, total_score=rp.score, max_combo=rp.max_combo, rounds_played=rp.rounds_played, avg_time=round(avg_time, 1), rank=rank))
        if u.id == current_user.id:
            my_exp_gained = rewards["exp"]
            my_points_gained = rewards["points"]
        rank += 1
    await db.flush()
    for res_item in results:
        u_result = await db.execute(select(User).where(User.id == res_item.user_id))
        u_obj = u_result.scalar_one_or_none()
        if u_obj:
            new_pairs = await sync_user_achievements(db, u_obj)
            if u_obj.id == current_user.id:
                all_new_achievements = [achievement.name for _, achievement in new_pairs]
    await db.commit()
    return RelayEndResponse(room_id=room.id, total_rounds=room.current_round, duration=duration, results=results, exp_gained=my_exp_gained, points_gained=my_points_gained, new_achievements=all_new_achievements)


@router.get("/history", response_model=RelayHistoryResponse)
async def get_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(RelayRoom, RelayPlayer).join(RelayPlayer, and_(RelayRoom.id == RelayPlayer.room_id, RelayPlayer.user_id == current_user.id)).where(RelayRoom.status == "finished").order_by(desc(RelayRoom.finished_at))
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = []
    for room, player in result.all():
        duration = int((room.finished_at - room.started_at).total_seconds()) if room.started_at and room.finished_at else 0
        items.append(RelayHistoryItem(room_id=room.id, mode=room.mode, difficulty=room.difficulty, total_rounds=room.current_round, total_score=player.score, max_combo=player.max_combo, duration=duration, result="completed", played_at=room.finished_at or room.created_at))
    return RelayHistoryResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/rankings", response_model=RelayRankingResponse)
async def get_rankings(period: str = Query("all"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    query = select(
        RelayPlayer.user_id,
        func.sum(RelayPlayer.score).label("total_score"),
        func.count(RelayPlayer.id).label("total_games"),
        func.max(RelayPlayer.max_combo).label("max_combo"),
        func.max(RelayPlayer.rounds_played).label("best_rounds")
    ).join(RelayRoom, RelayPlayer.room_id == RelayRoom.id).where(RelayRoom.status == "finished").group_by(RelayPlayer.user_id).order_by(desc("total_score"))
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = []
    rank = (page - 1) * page_size + 1
    for row in result.all():
        u_result = await db.execute(select(User).where(User.id == row.user_id))
        u = u_result.scalar_one_or_none()
        if u:
            items.append(RelayRankingItem(rank=rank, user_id=u.id, username=u.username, avatar_url=u.avatar_url, total_score=row.total_score or 0, total_games=row.total_games or 0, max_combo=row.max_combo or 0, best_rounds=row.best_rounds or 0, win_rate=0.0))
            rank += 1
    return RelayRankingResponse(items=items, total=total, period=period)

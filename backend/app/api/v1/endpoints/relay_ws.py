import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timezone
from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.core.relay_manager import relay_manager, PlayerConnection, RoomState
from app.core.levels import calculate_level, calculate_relay_rewards
from app.core.achievement_sync import sync_user_achievements
from app.models.relay import RelayRoom, RelayPlayer, RelayRound
from app.models.poem import Poem
from app.models.user import User
import random

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


async def authenticate_ws(token: str) -> dict:
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return {"id": user.id, "username": user.username, "avatar_url": user.avatar_url}


def get_last_char(verse: str) -> str:
    clean = verse.rstrip('\u3002\uff0c\uff01\uff1f\u3001\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09')
    return clean[-1] if clean else verse[-1]


async def get_random_starter_verse(db) -> dict:
    count_result = await db.execute(select(Poem).limit(1))
    from sqlalchemy import func as sqlfunc
    count_result = await db.execute(select(sqlfunc.count()).select_from(Poem))
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


async def validate_verse_db(db, verse: str, expected_char: str) -> dict:
    first_char = verse[0] if verse else ""
    if first_char != expected_char:
        return {"is_valid": False, "match_type": "none", "poem_title": None, "author": None}
    result = await db.execute(select(Poem).where(Poem.content.contains(verse)).limit(1))
    poem = result.scalar_one_or_none()
    if poem:
        return {"is_valid": True, "match_type": "exact", "poem_title": poem.title, "author": poem.author}
    return {"is_valid": True, "match_type": "exact", "poem_title": None, "author": None}


async def find_matching_verses_db(db, char: str, limit: int = 20) -> list:
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


def build_players_info(room_state: RoomState) -> list:
    players = []
    for uid, conn in room_state.connections.items():
        players.append({
            "user_id": uid,
            "username": conn.username,
            "avatar_url": conn.avatar_url,
            "is_host": (uid == room_state.turn_order[0] if room_state.turn_order else False),
            "is_ready": room_state.is_user_ready(uid),
            "connected": True
        })
    for uid in room_state.disconnected_users:
        players.append({
            "user_id": uid,
            "username": f"player_{uid}",
            "avatar_url": None,
            "is_host": (uid == room_state.turn_order[0] if room_state.turn_order else False),
            "is_ready": False,
            "connected": False
        })
    return players


async def handle_turn_timeout(room_id: int, user_id: int, time_limit: int):
    await asyncio.sleep(time_limit)
    room = relay_manager.get_room(room_id)
    if not room or room.status != "playing":
        return
    if room.current_turn_user_id != user_id:
        return
    async with AsyncSessionLocal() as db:
        player_result = await db.execute(
            select(RelayPlayer).where(and_(RelayPlayer.room_id == room_id, RelayPlayer.user_id == user_id))
        )
        player = player_result.scalar_one_or_none()
        if player:
            player.combo = 0
            await db.commit()
    room.advance_turn()
    next_uid = room.current_turn_user_id
    next_conn = room.connections.get(next_uid)
    await relay_manager.broadcast(room_id, {
        "type": "turn_timeout",
        "user_id": user_id,
        "next_turn": {
            "user_id": next_uid,
            "username": next_conn.username if next_conn else ""
        }
    })
    db_room_result = None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        db_room = result.scalar_one_or_none()
        if db_room:
            db_room.current_turn_user_id = next_uid
            await db.commit()
    async with AsyncSessionLocal() as db2:
        result2 = await db2.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        db_room2 = result2.scalar_one_or_none()
        tl = db_room2.time_limit if db_room2 else 30
    room.turn_timer_task = asyncio.create_task(
        handle_turn_timeout(room_id, next_uid, tl)
    )


async def start_turn_timer(room_id: int, user_id: int, time_limit: int):
    room = relay_manager.get_room(room_id)
    if not room:
        return
    if room.turn_timer_task and not room.turn_timer_task.done():
        room.turn_timer_task.cancel()
    room.turn_timer_task = asyncio.create_task(
        handle_turn_timeout(room_id, user_id, time_limit)
    )


@router.websocket("/ws/relay/{room_id}")
async def relay_websocket(websocket: WebSocket, room_id: int, token: str = Query(...)):
    user_info = await authenticate_ws(token)
    if not user_info:
        await websocket.close(code=4001, reason="认证失败")
        return

    await websocket.accept()
    user_id = user_info["id"]
    username = user_info["username"]
    avatar_url = user_info.get("avatar_url")

    relay_manager.purge_expired_rooms()

    async with AsyncSessionLocal() as db:
        room_result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        db_room = room_result.scalar_one_or_none()
        if not db_room:
            await websocket.send_text(json.dumps({"type": "error", "message": "房间不存在"}, ensure_ascii=False))
            await websocket.close()
            return

        player_result = await db.execute(
            select(RelayPlayer).where(and_(RelayPlayer.room_id == room_id, RelayPlayer.user_id == user_id))
        )
        if not player_result.scalar_one_or_none():
            await websocket.send_text(json.dumps({"type": "error", "message": "你不在该房间中"}, ensure_ascii=False))
            await websocket.close()
            return

        room_state = relay_manager.get_or_create_room(room_id, db_room.room_code, db_room.max_players or 2)

    player_conn = PlayerConnection(websocket, user_id, username, avatar_url)

    is_reconnect = user_id in (room_state.disconnected_users or {})
    if is_reconnect:
        await relay_manager.reconnect(room_id, player_conn)
    else:
        await relay_manager.connect(room_id, player_conn)

    if is_reconnect and room_state.status == "playing" and room_state.game_snapshot:
        await relay_manager.send_to_user(room_id, user_id, {
            "type": "game_state_sync",
            **room_state.game_snapshot
        })
        await relay_manager.broadcast(room_id, {
            "type": "player_reconnected",
            "user_id": user_id,
            "username": username,
            "players": build_players_info(room_state),
            "player_count": room_state.player_count
        }, exclude_user=user_id)
    else:
        await relay_manager.broadcast(room_id, {
            "type": "player_joined",
            "user_id": user_id,
            "username": username,
            "avatar_url": avatar_url,
            "players": build_players_info(room_state),
            "player_count": room_state.player_count,
            "max_players": room_state.max_players
        })

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action = msg.get("action")

            if action == "start_game":
                await handle_start_game(room_id, user_id, room_state)

            elif action == "ready":
                await handle_ready(room_id, user_id, room_state)

            elif action == "submit_verse":
                verse = msg.get("verse", "").strip()
                if verse:
                    await handle_submit_verse(room_id, user_id, verse, room_state)

            elif action == "request_hint":
                await handle_request_hint(room_id, user_id)

            elif action == "chat":
                content = msg.get("content", "").strip()
                if content:
                    await relay_manager.broadcast(room_id, {
                        "type": "chat",
                        "user_id": user_id,
                        "username": username,
                        "content": content[:200]
                    })

            elif action == "end_game":
                await handle_end_game(room_id, user_id, room_state)

            elif action == "rematch":
                await handle_rematch(room_id, user_id, room_state)

            elif action == "kick":
                target_id = msg.get("target_user_id")
                if target_id:
                    await handle_kick(room_id, user_id, int(target_id), room_state)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error room={room_id} user={user_id}: {e}")
    finally:
        await relay_manager.disconnect(room_id, user_id)
        room = relay_manager.get_room(room_id)
        if room:
            if user_id in room.kicked_users:
                room.kicked_users.discard(user_id)
                return
            is_temp_disconnect = room.status == "playing" and user_id in room.disconnected_users
            await relay_manager.broadcast(room_id, {
                "type": "player_disconnected" if is_temp_disconnect else "player_left",
                "user_id": user_id,
                "username": username,
                "players": build_players_info(room),
                "player_count": room.player_count,
                "can_reconnect": is_temp_disconnect
            })
            if room.status == "playing" and room.player_count == 0 and not room.disconnected_users:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
                    db_room = result.scalar_one_or_none()
                    if db_room and db_room.status == "playing":
                        db_room.status = "finished"
                        db_room.finished_at = datetime.now(timezone.utc)
                        await db.commit()
                relay_manager.cleanup_room(room_id)


async def handle_ready(room_id: int, user_id: int, room_state: RoomState):
    if room_state.status != "waiting":
        return
    was_ready = room_state.is_user_ready(user_id)
    room_state.set_ready(user_id, not was_ready)
    await relay_manager.broadcast(room_id, {
        "type": "ready_changed",
        "user_id": user_id,
        "is_ready": not was_ready,
        "all_ready": room_state.all_ready,
        "players": build_players_info(room_state)
    })


async def handle_start_game(room_id: int, user_id: int, room_state: RoomState):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        room = result.scalar_one_or_none()
        if not room:
            return
        if room.host_id != user_id:
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "只有房主可以开始游戏"
            })
            return
        if room.status != "waiting":
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "游戏已开始或已结束"
            })
            return
        if room_state.player_count < 2:
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "至少需要2名玩家才能开始"
            })
            return
        if not room_state.all_ready:
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "还有玩家未准备"
            })
            return

        starter = await get_random_starter_verse(db)
        next_char = get_last_char(starter["verse"])

        room.status = "playing"
        room.current_round = 1
        room.next_char = next_char
        room.started_at = datetime.now(timezone.utc)

        first_turn_uid = room_state.turn_order[0] if room_state.turn_order else user_id
        room.current_turn_user_id = first_turn_uid

        first_round = RelayRound(
            room_id=room.id, round_number=1, user_id=0,
            verse=starter["verse"], poem_title=starter["poem_title"],
            author=starter["author"], match_type="starter", score=0, time_used=0
        )
        db.add(first_round)
        await db.commit()

        room_state.status = "playing"
        room_state.current_turn_index = 0

        first_conn = room_state.connections.get(first_turn_uid)

        initial_rounds = [{
            "user_id": 0, "username": "系统",
            "verse": starter["verse"], "poem_title": starter["poem_title"],
            "author": starter["author"], "score": 0
        }]
        room_state.update_snapshot({
            "next_char": next_char,
            "current_round": 1,
            "max_rounds": room.max_rounds,
            "time_limit": room.time_limit,
            "current_turn": {
                "user_id": first_turn_uid,
                "username": first_conn.username if first_conn else ""
            },
            "players": build_players_info(room_state),
            "rounds": initial_rounds,
            "players_scores": []
        })

        await relay_manager.broadcast(room_id, {
            "type": "game_started",
            "starter_verse": starter["verse"],
            "starter_poem_title": starter["poem_title"],
            "starter_author": starter["author"],
            "next_char": next_char,
            "current_round": 1,
            "max_rounds": room.max_rounds,
            "time_limit": room.time_limit,
            "current_turn": {
                "user_id": first_turn_uid,
                "username": first_conn.username if first_conn else ""
            },
            "players": build_players_info(room_state)
        })

        await start_turn_timer(room_id, first_turn_uid, room.time_limit)


async def handle_submit_verse(room_id: int, user_id: int, verse: str, room_state: RoomState):
    if room_state.current_turn_user_id != user_id:
        await relay_manager.send_to_user(room_id, user_id, {
            "type": "error", "message": "还没轮到你"
        })
        return

    if room_state.turn_timer_task and not room_state.turn_timer_task.done():
        room_state.turn_timer_task.cancel()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        room = result.scalar_one_or_none()
        if not room or room.status != "playing":
            return

        validation = await validate_verse_db(db, verse, room.next_char)
        player_result = await db.execute(
            select(RelayPlayer).where(and_(RelayPlayer.room_id == room_id, RelayPlayer.user_id == user_id))
        )
        player = player_result.scalar_one_or_none()
        if not player:
            return

        if not validation["is_valid"]:
            player.combo = 0
            await db.commit()
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "verse_invalid",
                "message": f"诗句首字与要求的「{room.next_char}」不匹配"
            })
            return

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

        new_round = RelayRound(
            room_id=room.id, round_number=room.current_round,
            user_id=user_id, verse=verse,
            poem_title=validation.get("poem_title"),
            author=validation.get("author"),
            match_type=validation["match_type"],
            score=score, time_used=0
        )
        db.add(new_round)

        game_finished = room.current_round >= room.max_rounds
        if game_finished:
            room.status = "finished"
            room.finished_at = datetime.now(timezone.utc)
            room_state.status = "finished"

        room_state.advance_turn()
        next_turn_uid = room_state.current_turn_user_id
        room.current_turn_user_id = next_turn_uid

        await db.commit()

        conn = room_state.connections.get(user_id)
        next_conn = room_state.connections.get(next_turn_uid)

        players_scores = []
        all_players_result = await db.execute(
            select(RelayPlayer, User).join(User, RelayPlayer.user_id == User.id)
            .where(RelayPlayer.room_id == room_id)
        )
        for rp, u in all_players_result.all():
            players_scores.append({
                "user_id": u.id,
                "username": u.username,
                "score": rp.score,
                "combo": rp.combo,
                "max_combo": rp.max_combo,
                "rounds_played": rp.rounds_played
            })

        next_turn_info = {
            "user_id": next_turn_uid,
            "username": next_conn.username if next_conn else ""
        } if not game_finished else None

        await relay_manager.broadcast(room_id, {
            "type": "verse_accepted",
            "user_id": user_id,
            "username": conn.username if conn else "",
            "verse": verse,
            "poem_title": validation.get("poem_title"),
            "author": validation.get("author"),
            "score": score,
            "combo": player.combo,
            "current_round": room.current_round,
            "next_char": next_char,
            "players_scores": players_scores,
            "game_finished": game_finished,
            "next_turn": next_turn_info
        })

        if room_state.game_snapshot and not game_finished:
            snap_rounds = room_state.game_snapshot.get("rounds", [])
            snap_rounds.append({
                "user_id": user_id,
                "username": conn.username if conn else "",
                "verse": verse,
                "poem_title": validation.get("poem_title"),
                "author": validation.get("author"),
                "score": score
            })
            room_state.update_snapshot({
                "next_char": next_char,
                "current_round": room.current_round,
                "max_rounds": room.max_rounds,
                "time_limit": room.time_limit,
                "current_turn": next_turn_info,
                "players": build_players_info(room_state),
                "rounds": snap_rounds,
                "players_scores": players_scores
            })

        if game_finished:
            await broadcast_game_result(room_id, room, db, room_state)
        else:
            await start_turn_timer(room_id, next_turn_uid, room.time_limit)


async def handle_request_hint(room_id: int, user_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        room = result.scalar_one_or_none()
        if not room or room.status != "playing":
            return
        player_result = await db.execute(
            select(RelayPlayer).where(and_(RelayPlayer.room_id == room_id, RelayPlayer.user_id == user_id))
        )
        player = player_result.scalar_one_or_none()
        if not player:
            return
        if player.hints_used >= 3:
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "提示次数已用完"
            })
            return
        matches = await find_matching_verses_db(db, room.next_char, limit=20)
        random.shuffle(matches)
        hints = matches[:3]
        if not hints:
            hints = [{"verse": f"{room.next_char}...", "poem_title": "暂无匹配", "author": "未知"}]
        player.hints_used += 1
        await db.commit()
        await relay_manager.send_to_user(room_id, user_id, {
            "type": "hint_response",
            "hints": hints,
            "hint_count_used": player.hints_used,
            "hint_count_max": 3
        })


async def handle_end_game(room_id: int, user_id: int, room_state: RoomState):
    if room_state.turn_timer_task and not room_state.turn_timer_task.done():
        room_state.turn_timer_task.cancel()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        room = result.scalar_one_or_none()
        if not room:
            return
        if room.host_id != user_id:
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "只有房主可以结束游戏"
            })
            return
        if room.status == "finished":
            return
        room.status = "finished"
        room.finished_at = datetime.now(timezone.utc)
        room_state.status = "finished"
        await db.commit()
        await broadcast_game_result(room_id, room, db, room_state)


async def broadcast_game_result(room_id: int, room: RelayRoom, db: AsyncSession, room_state: RoomState):
    duration = int((room.finished_at - room.started_at).total_seconds()) if room.started_at and room.finished_at else 0
    players_result = await db.execute(
        select(RelayPlayer, User).join(User, RelayPlayer.user_id == User.id)
        .where(RelayPlayer.room_id == room_id).order_by(desc(RelayPlayer.score))
    )
    results = []
    rank = 1
    for rp, u in players_result.all():
        avg_time = rp.total_time / rp.rounds_played if rp.rounds_played > 0 else 0
        rewards = calculate_relay_rewards(rp.score)
        exp_gained = rewards["exp"]
        u.exp = (u.exp or 0) + exp_gained
        u.points = (u.points or 0) + rewards["points"]
        u.level = calculate_level(u.exp)
        results.append({
            "user_id": u.id,
            "username": u.username,
            "avatar_url": u.avatar_url,
            "total_score": rp.score,
            "max_combo": rp.max_combo,
            "rounds_played": rp.rounds_played,
            "avg_time": round(avg_time, 1),
            "rank": rank,
            "exp_gained": exp_gained,
            "points_gained": rewards["points"]
        })
        rank += 1
    await db.commit()
    for rp_u in results:
        uid = rp_u["user_id"]
        async with AsyncSessionLocal() as sync_db:
            u_result = await sync_db.execute(select(User).where(User.id == uid))
            u_obj = u_result.scalar_one_or_none()
            if u_obj:
                await sync_user_achievements(sync_db, u_obj)
                await sync_db.commit()

    await relay_manager.broadcast(room_id, {
        "type": "game_ended",
        "total_rounds": room.current_round,
        "duration": duration,
        "results": results
    })


async def handle_rematch(room_id: int, user_id: int, room_state: RoomState):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        old_room = result.scalar_one_or_none()
        if not old_room:
            return
        if old_room.host_id != user_id:
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "只有房主可以发起再来一局"
            })
            return
        if old_room.status != "finished":
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "游戏尚未结束"
            })
            return

        import string as _string
        code = ''.join(random.choices(_string.ascii_uppercase + _string.digits, k=8))
        new_room = RelayRoom(
            room_code=code, host_id=user_id,
            mode="multi", difficulty=old_room.difficulty,
            max_rounds=old_room.max_rounds, time_limit=old_room.time_limit,
            max_players=old_room.max_players, status="waiting",
            password=old_room.password
        )
        db.add(new_room)
        await db.flush()

        connected_uids = list(room_state.connections.keys())
        for uid in connected_uids:
            p = RelayPlayer(room_id=new_room.id, user_id=uid, is_host=(uid == user_id))
            db.add(p)
        await db.commit()
        await db.refresh(new_room)

        new_room_state = relay_manager.get_or_create_room(new_room.id, new_room.room_code, new_room.max_players or 2)

        for uid, conn in list(room_state.connections.items()):
            new_player_conn = PlayerConnection(conn.websocket, conn.user_id, conn.username, conn.avatar_url)
            new_room_state.connections[uid] = new_player_conn
            if uid not in new_room_state.turn_order:
                new_room_state.turn_order.append(uid)

        relay_manager.cleanup_room(room_id)

        await relay_manager.broadcast(new_room.id, {
            "type": "rematch_created",
            "new_room_id": new_room.id,
            "new_room_code": new_room.room_code,
            "players": build_players_info(new_room_state),
            "player_count": new_room_state.player_count,
            "max_players": new_room_state.max_players
        })


async def handle_kick(room_id: int, user_id: int, target_id: int, room_state: RoomState):
    if room_state.status != "waiting":
        await relay_manager.send_to_user(room_id, user_id, {
            "type": "error", "message": "游戏进行中无法踢人"
        })
        return
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RelayRoom).where(RelayRoom.id == room_id))
        room = result.scalar_one_or_none()
        if not room or room.host_id != user_id:
            await relay_manager.send_to_user(room_id, user_id, {
                "type": "error", "message": "只有房主可以踢人"
            })
            return
        if target_id == user_id:
            return
        target_conn = room_state.connections.get(target_id)
        target_name = target_conn.username if target_conn else ""
        await db.execute(
            select(RelayPlayer).where(
                and_(RelayPlayer.room_id == room_id, RelayPlayer.user_id == target_id)
            )
        )
        from sqlalchemy import delete as sa_delete
        await db.execute(
            sa_delete(RelayPlayer).where(
                and_(RelayPlayer.room_id == room_id, RelayPlayer.user_id == target_id)
            )
        )
        await db.commit()

    await relay_manager.send_to_user(room_id, target_id, {
        "type": "kicked", "message": "你被房主移出了房间"
    })
    await asyncio.sleep(0.3)
    room_state.kicked_users.add(target_id)

    if target_id in room_state.connections:
        conn = room_state.connections[target_id]
        del room_state.connections[target_id]
        try:
            await conn.websocket.close(code=4001, reason="kicked")
        except Exception:
            pass
    if target_id in room_state.turn_order:
        room_state.turn_order.remove(target_id)
    room_state.ready_users.discard(target_id)

    await relay_manager.broadcast(room_id, {
        "type": "player_kicked",
        "user_id": target_id,
        "username": target_name,
        "players": build_players_info(room_state),
        "player_count": room_state.player_count
    })

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("uvicorn.error")

ROOM_EXPIRE_MINUTES = 30
DISCONNECT_GRACE_SECONDS = 60


class PlayerConnection:
    def __init__(self, websocket: WebSocket, user_id: int, username: str, avatar_url: Optional[str] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.username = username
        self.avatar_url = avatar_url
        self.connected_at = datetime.now(timezone.utc)


class RoomState:
    def __init__(self, room_id: int, room_code: str, max_players: int = 2):
        self.room_id = room_id
        self.room_code = room_code
        self.max_players = max_players
        self.connections: Dict[int, PlayerConnection] = {}
        self.turn_order: List[int] = []
        self.current_turn_index: int = 0
        self.turn_timer_task: Optional[asyncio.Task] = None
        self.status: str = "waiting"
        self.ready_users: Set[int] = set()
        self.disconnected_users: Dict[int, datetime] = {}
        self.kicked_users: Set[int] = set()
        self.created_at: datetime = datetime.now(timezone.utc)
        self.game_snapshot: Optional[dict] = None

    @property
    def current_turn_user_id(self) -> Optional[int]:
        if not self.turn_order:
            return None
        idx = self.current_turn_index % len(self.turn_order)
        return self.turn_order[idx]

    def advance_turn(self):
        if self.turn_order:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)

    @property
    def player_count(self) -> int:
        return len(self.connections)

    @property
    def total_player_count(self) -> int:
        return len(self.connections) + len(self.disconnected_users)

    @property
    def is_full(self) -> bool:
        return self.total_player_count >= self.max_players

    @property
    def all_ready(self) -> bool:
        if self.player_count < 2:
            return False
        for uid in self.connections:
            host_uid = self.turn_order[0] if self.turn_order else None
            if uid == host_uid:
                continue
            if uid not in self.ready_users:
                return False
        return True

    def set_ready(self, user_id: int, ready: bool):
        if ready:
            self.ready_users.add(user_id)
        else:
            self.ready_users.discard(user_id)

    def is_user_ready(self, user_id: int) -> bool:
        return user_id in self.ready_users

    def update_snapshot(self, snapshot: dict):
        self.game_snapshot = snapshot

    def is_expired(self) -> bool:
        if self.status != "waiting":
            return False
        return datetime.now(timezone.utc) - self.created_at > timedelta(minutes=ROOM_EXPIRE_MINUTES)


class RelayConnectionManager:
    def __init__(self):
        self.rooms: Dict[int, RoomState] = {}
        self._lock = asyncio.Lock()

    def get_or_create_room(self, room_id: int, room_code: str, max_players: int = 2) -> RoomState:
        if room_id not in self.rooms:
            self.rooms[room_id] = RoomState(room_id, room_code, max_players)
        return self.rooms[room_id]

    def get_room(self, room_id: int) -> Optional[RoomState]:
        return self.rooms.get(room_id)

    async def connect(self, room_id: int, player: PlayerConnection) -> RoomState:
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                return None
            room.connections[player.user_id] = player
            if player.user_id not in room.turn_order:
                room.turn_order.append(player.user_id)
            return room

    async def disconnect(self, room_id: int, user_id: int):
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                return
            room.connections.pop(user_id, None)
            room.ready_users.discard(user_id)
            if room.status == "playing":
                room.disconnected_users[user_id] = datetime.now(timezone.utc)
            if not room.connections and not room.disconnected_users:
                if room.turn_timer_task and not room.turn_timer_task.done():
                    room.turn_timer_task.cancel()
                self.rooms.pop(room_id, None)

    async def reconnect(self, room_id: int, player: PlayerConnection) -> Optional[RoomState]:
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                return None
            room.connections[player.user_id] = player
            room.disconnected_users.pop(player.user_id, None)
            return room

    def purge_expired_rooms(self) -> List[int]:
        now = datetime.now(timezone.utc)
        expired_ids = []
        for rid, room in list(self.rooms.items()):
            if room.is_expired():
                expired_ids.append(rid)
            if room.status == "playing":
                stale = [uid for uid, t in room.disconnected_users.items()
                         if (now - t).total_seconds() > DISCONNECT_GRACE_SECONDS]
                for uid in stale:
                    room.disconnected_users.pop(uid, None)
                    if uid in room.turn_order:
                        room.turn_order.remove(uid)
        for rid in expired_ids:
            room = self.rooms.pop(rid, None)
            if room and room.turn_timer_task and not room.turn_timer_task.done():
                room.turn_timer_task.cancel()
        return expired_ids

    async def broadcast(self, room_id: int, message: dict, exclude_user: Optional[int] = None):
        room = self.rooms.get(room_id)
        if not room:
            return
        data = json.dumps(message, ensure_ascii=False, default=str)
        disconnected = []
        for uid, conn in room.connections.items():
            if exclude_user and uid == exclude_user:
                continue
            try:
                await conn.websocket.send_text(data)
            except Exception:
                disconnected.append(uid)
        for uid in disconnected:
            room.connections.pop(uid, None)

    async def send_to_user(self, room_id: int, user_id: int, message: dict):
        room = self.rooms.get(room_id)
        if not room:
            return
        conn = room.connections.get(user_id)
        if not conn:
            return
        try:
            data = json.dumps(message, ensure_ascii=False, default=str)
            await conn.websocket.send_text(data)
        except Exception:
            room.connections.pop(user_id, None)

    def cleanup_room(self, room_id: int):
        room = self.rooms.pop(room_id, None)
        if room and room.turn_timer_task and not room.turn_timer_task.done():
            room.turn_timer_task.cancel()


relay_manager = RelayConnectionManager()

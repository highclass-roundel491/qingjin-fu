from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RelayGameMode(str, enum.Enum):
    SINGLE = "single"
    MULTI = "multi"


class RelayDifficulty(str, enum.Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class RelayGameStatus(str, enum.Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class RelayRoom(Base):
    __tablename__ = "relay_rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(20), unique=True, nullable=False, index=True)
    host_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mode = Column(String(20), default=RelayGameMode.SINGLE, nullable=False)
    difficulty = Column(String(20), default=RelayDifficulty.NORMAL, nullable=False)
    status = Column(String(20), default=RelayGameStatus.WAITING, nullable=False, index=True)
    max_rounds = Column(Integer, default=20)
    time_limit = Column(Integer, default=30)
    current_round = Column(Integer, default=0)
    next_char = Column(String(10), nullable=True)
    current_turn_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    max_players = Column(Integer, default=2)
    password = Column(String(20), nullable=True)
    turn_time_left = Column(Integer, default=30)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RelayPlayer(Base):
    __tablename__ = "relay_players"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("relay_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, default=0)
    combo = Column(Integer, default=0)
    max_combo = Column(Integer, default=0)
    rounds_played = Column(Integer, default=0)
    total_time = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)
    is_host = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class RelayRound(Base):
    __tablename__ = "relay_rounds"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("relay_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    verse = Column(String(200), nullable=False)
    poem_title = Column(String(200), nullable=True)
    author = Column(String(100), nullable=True)
    match_type = Column(String(20), nullable=True)
    score = Column(Integer, default=0)
    time_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

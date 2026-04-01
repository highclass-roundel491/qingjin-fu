from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class FeiHuaLingGame(Base):
    __tablename__ = "feihualing_games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(10), nullable=False)
    status = Column(String(20), default="playing")
    user_score = Column(Integer, default=0)
    ai_score = Column(Integer, default=0)
    total_rounds = Column(Integer, default=0)
    result = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="feihualing_games")
    rounds = relationship("FeiHuaLingRound", back_populates="game", cascade="all, delete-orphan")

class FeiHuaLingRound(Base):
    __tablename__ = "feihualing_rounds"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(UUID(as_uuid=True), ForeignKey("feihualing_games.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    player = Column(String(10), nullable=False)
    poem_content = Column(Text, nullable=False)
    poem_id = Column(Integer, ForeignKey("poems.id", ondelete="SET NULL"))
    poem_author = Column(String(100))
    poem_title = Column(String(200))
    poem_dynasty = Column(String(50))
    response_time = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("FeiHuaLingGame", back_populates="rounds")
    poem = relationship("Poem")

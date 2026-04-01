from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(20), nullable=False)
    duration = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PoemFavorite(Base):
    __tablename__ = "poem_favorites"
    __table_args__ = (
        UniqueConstraint('user_id', 'poem_id', name='uq_poem_favorite_user_poem'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_learned = Column(Integer, default=0)
    total_favorites = Column(Integer, default=0)
    study_time = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_study_date = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

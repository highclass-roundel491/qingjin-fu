from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base


class TimedChallengeSession(Base):
    __tablename__ = "timed_challenge_sessions"
    __table_args__ = (
        Index("idx_timed_sessions_user_status_started_at", "user_id", "status", "started_at"),
        Index("idx_timed_sessions_status_started_at", "status", "started_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False, default="medium")
    question_type = Column(String(20), nullable=False, default="mixed")
    total_questions = Column(Integer, nullable=False, default=10)
    answered_count = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    total_score = Column(Integer, nullable=False, default=0)
    combo = Column(Integer, nullable=False, default=0)
    max_combo = Column(Integer, nullable=False, default=0)
    time_per_question = Column(Integer, nullable=False, default=15)
    status = Column(String(20), nullable=False, default="active")
    exp_gained = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))


class TimedChallengeAnswer(Base):
    __tablename__ = "timed_challenge_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("timed_challenge_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_index = Column(Integer, nullable=False)
    question_type = Column(String(20), nullable=False)
    poem_id = Column(Integer, ForeignKey("poems.id", ondelete="SET NULL"), nullable=True)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    user_answer = Column(Text)
    is_correct = Column(Boolean, nullable=False, default=False)
    time_spent = Column(Integer, nullable=False, default=0)
    score = Column(Integer, nullable=False, default=0)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

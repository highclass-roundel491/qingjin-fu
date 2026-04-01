from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class DailyChallenge(Base):
    __tablename__ = "daily_challenges"

    id = Column(Integer, primary_key=True, index=True)
    challenge_type = Column(String(20), nullable=False, default="fill_blank", index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_daily = Column(Boolean, default=False)
    date = Column(Date, nullable=True, index=True)
    sentence_template = Column(Text, nullable=False)
    sentence_template_2 = Column(Text)
    blank_count = Column(Integer, nullable=False, default=1)
    theme = Column(String(50))
    mood = Column(String(50))
    hint = Column(String(200))
    original_answer = Column(String(10))
    original_answer_2 = Column(String(10))
    difficulty = Column(String(20), default="medium")
    status = Column(String(20), default="active")
    response_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChallengeSubmission(Base):
    __tablename__ = "challenge_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("daily_challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    answer = Column(String(50), nullable=False)
    answer_2 = Column(String(50))
    content = Column(Text)
    ai_score = Column(Integer, default=0)
    ai_feedback = Column(Text)
    beauty_score = Column(Integer, default=0)
    creativity_score = Column(Integer, default=0)
    mood_score = Column(Integer, default=0)
    exp_gained = Column(Integer, default=0)
    points_gained = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

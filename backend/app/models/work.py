from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class WorkStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    genre = Column(String(50), nullable=False)
    status = Column(String(20), default=WorkStatus.DRAFT, nullable=False, index=True)
    ai_grammar_score = Column(Integer, nullable=True)
    ai_artistic_score = Column(Integer, nullable=True)
    ai_total_score = Column(Integer, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    exp_awarded = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)


class WorkLike(Base):
    __tablename__ = "work_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    work_id = Column(Integer, ForeignKey("works.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

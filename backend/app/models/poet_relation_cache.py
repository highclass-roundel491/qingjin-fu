from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class PoetRelationCache(Base):
    __tablename__ = "poet_relation_cache"

    id = Column(Integer, primary_key=True, index=True)
    poet_a = Column(String(50), nullable=False)
    poet_b = Column(String(50), nullable=False)
    cache_key = Column(String(120), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=False, default="")
    sections = Column(JSONB, nullable=False, default=[])
    known_relation = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

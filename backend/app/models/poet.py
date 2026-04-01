from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Poet(Base):
    __tablename__ = "poets"
    __table_args__ = (
        UniqueConstraint("name", "dynasty", name="uq_poets_name_dynasty"),
        Index("idx_poets_influence", "influence_score"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    dynasty = Column(String(50), nullable=False, index=True)
    alias = Column(String(200))
    birth_year = Column(String(50))
    death_year = Column(String(50))
    birth_death_desc = Column(String(100))
    styles = Column(Text)
    brief = Column(Text)
    detailed_bio = Column(Text)
    representative_works = Column(Text)
    influence_score = Column(Integer, default=50)
    poem_count = Column(Integer, default=0)
    portrait_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

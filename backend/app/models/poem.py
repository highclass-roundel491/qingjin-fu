from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY, Index
from sqlalchemy.sql import func
from app.core.database import Base

class Poem(Base):
    __tablename__ = "poems"
    __table_args__ = (
        Index("idx_poems_genre", "genre"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(50), nullable=False, index=True)
    dynasty = Column(String(20), nullable=False, index=True)
    content = Column(Text, nullable=False)
    translation = Column(Text)
    annotation = Column(Text)
    background = Column(Text)
    appreciation = Column(Text)
    category = Column(String(50), index=True)
    genre = Column(String(50))
    tags = Column(String(200))
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

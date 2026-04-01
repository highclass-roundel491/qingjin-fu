from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PoetBase(BaseModel):
    name: str
    dynasty: str
    alias: Optional[str] = None
    birth_year: Optional[str] = None
    death_year: Optional[str] = None
    birth_death_desc: Optional[str] = None
    styles: Optional[str] = None
    brief: Optional[str] = None
    detailed_bio: Optional[str] = None
    representative_works: Optional[str] = None
    influence_score: int = 50
    portrait_url: Optional[str] = None


class PoetCreate(PoetBase):
    pass


class PoetDetail(PoetBase):
    id: int
    poem_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PoetListItem(BaseModel):
    id: int
    name: str
    dynasty: str
    alias: Optional[str] = None
    birth_death_desc: Optional[str] = None
    styles: Optional[str] = None
    brief: Optional[str] = None
    influence_score: int = 50
    poem_count: int = 0

    class Config:
        from_attributes = True


class PoetListResponse(BaseModel):
    items: List[PoetListItem]
    total: int


class PoetBriefForPoem(BaseModel):
    id: int
    name: str
    dynasty: str
    alias: Optional[str] = None
    birth_death_desc: Optional[str] = None
    styles: Optional[str] = None
    brief: Optional[str] = None
    representative_works: Optional[str] = None
    influence_score: int = 50

    class Config:
        from_attributes = True

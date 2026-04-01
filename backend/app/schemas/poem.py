from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PoemBase(BaseModel):
    title: str
    author: str
    dynasty: str
    content: str
    translation: Optional[str] = None
    annotation: Optional[str] = None
    background: Optional[str] = None
    appreciation: Optional[str] = None
    category: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[str] = None

class PoemCreate(PoemBase):
    pass

class PoemUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    dynasty: Optional[str] = None
    content: Optional[str] = None
    translation: Optional[str] = None
    annotation: Optional[str] = None
    background: Optional[str] = None
    appreciation: Optional[str] = None
    category: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[str] = None

class PoemListItem(BaseModel):
    id: int
    title: str
    author: str
    dynasty: str
    content: str
    category: Optional[str] = None
    genre: Optional[str] = None
    view_count: int = 0
    favorite_count: int = 0

    class Config:
        from_attributes = True

class PoemDetail(PoemBase):
    id: int
    view_count: int = 0
    favorite_count: int = 0
    created_at: datetime
    updated_at: datetime
    is_favorited: bool = False

    class Config:
        from_attributes = True

class PoemListResponse(BaseModel):
    items: List[PoemListItem]
    total: int
    page: int
    page_size: int

class PoemSearchParams(BaseModel):
    keyword: str
    search_type: str = Field(default="content", pattern="^(title|author|content)$")

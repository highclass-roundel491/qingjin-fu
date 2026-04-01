from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    work_id: int
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    parent_id: Optional[int] = None
    reply_to_username: Optional[str] = None
    content: str
    like_count: int = 0
    is_liked: bool = False
    created_at: datetime
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class WorkCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    genre: str = Field(..., min_length=1, max_length=50)


class WorkUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    genre: Optional[str] = Field(None, min_length=1, max_length=50)


class WorkAIScore(BaseModel):
    grammar_score: int
    artistic_score: int
    total_score: int
    feedback: str


class WorkResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    genre: str
    status: str
    ai_grammar_score: Optional[int]
    ai_artistic_score: Optional[int]
    ai_total_score: Optional[int]
    ai_feedback: Optional[str]
    like_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class WorkListItem(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_url: Optional[str]
    title: str
    content: str
    genre: str
    status: str
    ai_total_score: Optional[int]
    like_count: int
    view_count: int
    is_liked: bool = False
    created_at: datetime
    published_at: Optional[datetime]


class WorkDetailResponse(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_url: Optional[str]
    title: str
    content: str
    genre: str
    status: str
    ai_grammar_score: Optional[int]
    ai_artistic_score: Optional[int]
    ai_total_score: Optional[int]
    ai_feedback: Optional[str]
    like_count: int
    view_count: int
    comment_count: int = 0
    is_liked: bool = False
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]


class WorkListResponse(BaseModel):
    items: List[WorkListItem]
    total: int
    page: int
    page_size: int


class WorkRankingItem(BaseModel):
    rank: int
    user_id: int
    username: str
    avatar_url: Optional[str]
    exp: int = 0
    level: int = 1
    work_count: int
    total_likes: int
    avg_score: Optional[float]


class WorkRankingResponse(BaseModel):
    items: List[WorkRankingItem]
    total: int


class WorkPieceRankingItem(BaseModel):
    rank: int
    work_id: int
    title: str
    content: str
    genre: str
    user_id: int
    username: str
    avatar_url: Optional[str]
    like_count: int
    view_count: int
    ai_grammar_score: Optional[int]
    ai_artistic_score: Optional[int]
    ai_total_score: Optional[int]
    composite_score: float
    published_at: Optional[datetime]


class WorkPieceRankingResponse(BaseModel):
    items: List[WorkPieceRankingItem]
    total: int
    ranking_type: str
    period: str


class AIScoreRequest(BaseModel):
    genre: Optional[str] = None


class AIScoreResponse(BaseModel):
    work_id: int
    grammar_score: int
    artistic_score: int
    total_score: int
    feedback: str
    composite_score: float

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: Optional[str]
    nickname: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    level: int
    exp: int
    points: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UserProfileStats(BaseModel):
    total_study_time: int
    total_poems_learned: int
    total_questions_answered: int
    correct_rate: float
    total_works_created: int
    total_likes_received: int
    follower_count: int
    following_count: int


class UserExpHistoryItem(BaseModel):
    id: str
    source: str
    source_label: str
    title: str
    detail: str
    exp: int
    occurred_at: datetime


class UserExpHistoryResponse(BaseModel):
    items: List[UserExpHistoryItem]
    total: int
    page: int
    page_size: int

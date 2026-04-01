from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class FollowResponse(BaseModel):
    following_id: int
    following_username: str
    is_mutual: bool


class FollowingItem(BaseModel):
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    level: int = 1
    is_mutual: bool = False
    followed_at: datetime


class FollowingListResponse(BaseModel):
    items: List[FollowingItem]
    total: int
    page: int
    page_size: int


class FollowerItem(BaseModel):
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    level: int = 1
    is_following: bool = False
    followed_at: datetime


class FollowerListResponse(BaseModel):
    items: List[FollowerItem]
    total: int
    page: int
    page_size: int


class UserAchievementBrief(BaseModel):
    id: int
    code: str
    name: str
    description: str
    icon: str
    rarity: str
    unlocked_at: datetime


class RecentWorkBrief(BaseModel):
    id: int
    title: str
    genre: str
    like_count: int
    published_at: Optional[datetime] = None


class UserPublicProfile(BaseModel):
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    level: int = 1
    exp: int = 0
    following_count: int = 0
    follower_count: int = 0
    work_count: int = 0
    is_following: bool = False
    is_follower: bool = False
    achievements: List[UserAchievementBrief] = []
    recent_works: List[RecentWorkBrief] = []
    joined_at: datetime


class ActivityFeedItem(BaseModel):
    id: int
    type: str
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    content: str
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    created_at: datetime


class ActivityFeedResponse(BaseModel):
    items: List[ActivityFeedItem]
    total: int
    page: int
    page_size: int

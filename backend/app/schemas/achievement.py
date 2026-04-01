from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AchievementInfo(BaseModel):
    id: int
    code: str
    name: str
    description: str
    icon: str
    rarity: str
    condition_type: str
    condition_value: int
    exp_reward: int
    points_reward: int

    class Config:
        from_attributes = True


class AchievementCategory(BaseModel):
    category: str
    category_name: str
    achievements: List[AchievementInfo]


class AchievementListResponse(BaseModel):
    categories: List[AchievementCategory]


class UserAchievementItem(BaseModel):
    id: int
    code: str
    name: str
    description: str
    icon: str
    rarity: str
    category: str
    exp_reward: int
    points_reward: int
    unlocked_at: datetime


class UserAchievementResponse(BaseModel):
    unlocked: List[UserAchievementItem]
    newly_unlocked: List[UserAchievementItem] = []
    total_unlocked: int
    total_achievements: int
    completion_rate: float
    current_level: int
    current_exp: int
    next_level_exp: Optional[int]
    total_exp_rewarded: int
    total_points_rewarded: int


class AchievementProgressItem(BaseModel):
    achievement_id: int
    code: str
    name: str
    description: str
    icon: str
    rarity: str
    category: str
    condition_type: str
    exp_reward: int
    points_reward: int
    current_value: int
    target_value: int
    percentage: float
    is_unlocked: bool


class AchievementProgressResponse(BaseModel):
    progress: List[AchievementProgressItem]
    newly_unlocked: List[UserAchievementItem] = []

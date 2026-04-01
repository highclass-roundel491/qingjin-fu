from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LearningRecordCreate(BaseModel):
    poem_id: int
    action: str
    duration: int = 0

class UserStatsResponse(BaseModel):
    total_learned: int
    total_favorites: int
    study_time: int
    streak_days: int
    level: int
    exp: int
    next_level_exp: int

class FavoriteResponse(BaseModel):
    id: int
    poem_id: int
    created_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class FeiHuaLingGameStart(BaseModel):
    difficulty: Optional[int] = 10
    keyword: Optional[str] = None

class FeiHuaLingGameResponse(BaseModel):
    game_id: UUID
    keyword: str
    time_limit: int = 30
    target_rounds: int = 10
    ai_score: int = 0
    ai_first_round: Optional['AIRoundData'] = None

class PoemSubmit(BaseModel):
    game_id: UUID
    poem_content: str
    response_time: int
    target_rounds: Optional[int] = 10

class AIResponse(BaseModel):
    poem_content: str
    author: Optional[str] = None
    title: Optional[str] = None
    dynasty: Optional[str] = None

class AIRoundData(BaseModel):
    verse: str
    poem_title: Optional[str] = None
    author: Optional[str] = None
    dynasty: Optional[str] = None
    round_number: int = 0
    verified: bool = False

class PoemSubmitResponse(BaseModel):
    valid: bool
    message: str
    continue_game: bool
    user_score: int
    ai_score: int = 0
    round_number: int
    score_gained: int = 0
    combo: int = 0
    user_round_count: int = 0
    poem_author: Optional[str] = None
    poem_title: Optional[str] = None
    poem_dynasty: Optional[str] = None
    ai_round: Optional[AIRoundData] = None
    ai_failed: bool = False

class GameEndRequest(BaseModel):
    game_id: UUID
    reason: str

class HintResponse(BaseModel):
    hint: str
    author: str
    hint_cost: int = 0

class RoundHistory(BaseModel):
    round_number: int
    player: str
    poem_content: str
    author: Optional[str] = None
    title: Optional[str] = None
    dynasty: Optional[str] = None
    created_at: datetime

class GameResult(BaseModel):
    game_id: UUID
    result: str
    user_score: int
    ai_score: int = 0
    total_rounds: int
    user_round_count: int = 0
    keyword: str
    duration: int
    rounds: List[RoundHistory]

class GameHistoryItem(BaseModel):
    id: UUID
    keyword: str
    result: str
    user_score: int
    ai_score: int = 0
    total_rounds: int
    difficulty: Optional[int] = 10
    created_at: datetime

    class Config:
        from_attributes = True

class GameHistoryResponse(BaseModel):
    items: List[GameHistoryItem]
    total: int
    page: int
    page_size: int

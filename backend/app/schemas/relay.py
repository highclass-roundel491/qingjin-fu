from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class RelayRoomCreateRequest(BaseModel):
    mode: str = "single"
    difficulty: str = "normal"
    max_rounds: int = 20
    time_limit: int = 30
    max_players: int = 2
    password: Optional[str] = None


class RelayPlayerInfo(BaseModel):
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    score: int = 0
    combo: int = 0
    is_host: bool = False

    class Config:
        from_attributes = True


class RelayRoundInfo(BaseModel):
    round: int
    user_id: int
    username: str
    verse: str
    poem_title: Optional[str] = None
    author: Optional[str] = None
    score: int = 0
    time_used: int = 0


class RelayRoomResponse(BaseModel):
    id: int
    room_code: str
    mode: str
    difficulty: str
    max_rounds: int
    time_limit: int
    status: str
    host_id: int
    host_username: str = ""
    max_players: int = 2
    has_password: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class RelayRoomDetailResponse(BaseModel):
    id: int
    room_code: str
    mode: str
    difficulty: str
    status: str
    current_round: int
    max_rounds: int
    time_limit: int
    next_char: Optional[str] = None
    players: List[RelayPlayerInfo] = []
    rounds: List[RelayRoundInfo] = []


class RelayStartResponse(BaseModel):
    room_id: int
    status: str
    current_round: int
    starter_verse: str
    starter_poem_title: str
    starter_author: str
    next_char: str
    started_at: datetime


class RelaySubmitRequest(BaseModel):
    verse: str


class RelaySubmitResponse(BaseModel):
    round: int
    verse: str
    poem_title: Optional[str] = None
    author: Optional[str] = None
    is_valid: bool
    match_type: str
    score: int
    next_char: str
    time_used: int
    combo: int


class RelayHintItem(BaseModel):
    verse: str
    poem_title: str
    author: str


class RelayHintResponse(BaseModel):
    hints: List[RelayHintItem]
    hint_count_used: int
    hint_count_max: int = 3


class RelayEndResultItem(BaseModel):
    user_id: int
    username: str
    total_score: int
    max_combo: int
    rounds_played: int
    avg_time: float
    rank: int


class RelayEndResponse(BaseModel):
    room_id: int
    total_rounds: int
    duration: int
    results: List[RelayEndResultItem]
    exp_gained: int
    points_gained: int
    new_achievements: List[str] = []


class RelayHistoryItem(BaseModel):
    room_id: int
    mode: str
    difficulty: str
    total_rounds: int
    total_score: int
    max_combo: int
    duration: int
    result: str
    played_at: datetime


class RelayHistoryResponse(BaseModel):
    items: List[RelayHistoryItem]
    total: int
    page: int
    page_size: int


class RelayRankingItem(BaseModel):
    rank: int
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    total_score: int
    total_games: int
    max_combo: int
    best_rounds: int
    win_rate: float


class RelayRankingResponse(BaseModel):
    items: List[RelayRankingItem]
    total: int
    period: str


class RelayLobbyItem(BaseModel):
    id: int
    room_code: str
    difficulty: str
    max_rounds: int
    time_limit: int
    max_players: int = 2
    player_count: int = 0
    host_username: str = ""
    host_avatar: Optional[str] = None
    has_password: bool = False
    created_at: datetime


class RelayLobbyResponse(BaseModel):
    items: List[RelayLobbyItem]
    total: int
    page: int
    page_size: int

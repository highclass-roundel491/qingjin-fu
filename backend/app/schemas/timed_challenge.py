from pydantic import BaseModel, Field
import datetime as dt
from typing import Optional, List


class TimedChallengeStartRequest(BaseModel):
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    question_count: int = Field(10, ge=5, le=20)
    question_type: str = Field("mixed", pattern="^(fill_verse|author_guess|verse_match|mixed)$")


class QuestionOption(BaseModel):
    key: str
    text: str


class TimedQuestion(BaseModel):
    index: int
    question_type: str
    question_text: str
    options: List[QuestionOption]
    hint: Optional[str] = None
    poem_dynasty: Optional[str] = None
    time_limit: int = 15


class TimedChallengeStartResponse(BaseModel):
    session_id: int
    difficulty: str
    total_questions: int
    time_per_question: int
    first_question: TimedQuestion


class TimedAnswerRequest(BaseModel):
    session_id: int
    question_index: int
    answer: str
    time_spent: int = Field(0, ge=0)


class TimedAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    score_gained: int
    combo: int
    total_score: int
    correct_count: int
    answered_count: int
    poem_title: Optional[str] = None
    poem_author: Optional[str] = None
    poem_content: Optional[str] = None
    next_question: Optional[TimedQuestion] = None
    is_finished: bool = False


class TimedChallengeEndRequest(BaseModel):
    session_id: int


class TimedChallengeResult(BaseModel):
    session_id: int
    difficulty: str
    total_questions: int
    answered_count: int
    correct_count: int
    accuracy: float
    total_score: int
    max_combo: int
    exp_gained: int
    duration: int
    answers: List["TimedAnswerDetail"]


class TimedAnswerDetail(BaseModel):
    index: int
    question_type: str
    question_text: str
    correct_answer: str
    user_answer: Optional[str] = None
    is_correct: bool
    score: int
    time_spent: int


class TimedHistoryItem(BaseModel):
    id: int
    difficulty: str
    total_questions: int
    correct_count: int
    accuracy: float
    total_score: int
    max_combo: int
    exp_gained: int
    started_at: dt.datetime
    duration: int

    class Config:
        from_attributes = True


class TimedHistoryResponse(BaseModel):
    items: List[TimedHistoryItem]
    total: int
    page: int
    page_size: int
    best_score: int
    best_accuracy: float
    total_games: int


class TimedRankingItem(BaseModel):
    rank: int
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    total_score: int
    best_score: int
    total_games: int
    best_accuracy: float
    level: int
    exp: int


class TimedRankingResponse(BaseModel):
    items: List[TimedRankingItem]
    total: int
    period: str

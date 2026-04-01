from pydantic import BaseModel, Field, model_validator
import datetime as dt
from typing import Optional, List

class DailyChallengeResponse(BaseModel):
    id: int
    challenge_type: str = "fill_blank"
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    is_daily: bool = False
    date: Optional[dt.date] = None
    sentence_template: str
    sentence_template_2: Optional[str] = None
    blank_count: int = 1
    theme: Optional[str] = None
    mood: Optional[str] = None
    hint: Optional[str] = None
    difficulty: str = "medium"
    status: str = "active"
    original_answer: Optional[str] = None
    original_answer_2: Optional[str] = None
    response_count: int = 0
    created_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True

class ChallengeListResponse(BaseModel):
    items: List[DailyChallengeResponse]
    total: int
    page: int
    page_size: int

class ChallengeCreateRequest(BaseModel):
    challenge_type: str = Field(..., pattern="^(fill_blank|continue_line)$")
    sentence_template: str = Field(..., min_length=2, max_length=200)
    sentence_template_2: Optional[str] = None
    blank_count: int = Field(1, ge=1, le=5)
    original_answer: Optional[str] = None
    original_answer_2: Optional[str] = None
    theme: Optional[str] = None
    mood: Optional[str] = None
    hint: Optional[str] = None
    difficulty: str = "medium"

    @model_validator(mode='after')
    def validate_fill_blank(self):
        if self.challenge_type != 'fill_blank':
            return self
        t1 = self.sentence_template
        t1_blanks = t1.count('_') - t1.count('__') * 2 + t1.count('__')
        real_blanks_1 = t1.replace('__', '').count('_') if '__' not in t1 else t1.count('__')
        if '__' in t1:
            pass
        else:
            if t1.count('_') != 1:
                raise ValueError('\u4e0a\u8054\u5fc5\u987b\u6070\u597d\u5305\u542b\u4e00\u4e2a\u7a7a\u4f4d\uff08_\uff09')
        if not self.sentence_template_2:
            raise ValueError('\u586b\u5b57\u6311\u6218\u5fc5\u987b\u540c\u65f6\u63d0\u4f9b\u4e0a\u8054\u548c\u4e0b\u8054')
        t2 = self.sentence_template_2
        if '__' not in t2 and t2.count('_') != 1:
            raise ValueError('\u4e0b\u8054\u5fc5\u987b\u6070\u597d\u5305\u542b\u4e00\u4e2a\u7a7a\u4f4d\uff08_\uff09')
        if self.original_answer and len(self.original_answer) != 1:
            raise ValueError('\u4e0a\u8054\u7b54\u6848\u5fc5\u987b\u4e3a\u5355\u4e2a\u6c49\u5b57')
        if self.original_answer_2 and len(self.original_answer_2) != 1:
            raise ValueError('\u4e0b\u8054\u7b54\u6848\u5fc5\u987b\u4e3a\u5355\u4e2a\u6c49\u5b57')
        self.blank_count = 1
        return self

class ChallengeSubmitRequest(BaseModel):
    challenge_id: int
    answer: str
    answer_2: Optional[str] = None
    content: Optional[str] = None

class ChallengeSubmitResponse(BaseModel):
    id: int
    completed_sentence: str
    completed_sentence_2: Optional[str] = None
    exp_gained: int
    points_gained: int
    ai_score: int = 0
    beauty_score: int = 0
    creativity_score: int = 0
    mood_score: int = 0
    ai_feedback: Optional[str] = None
    ai_highlight: Optional[str] = None
    is_original_match: bool = False

class ChallengeResponseItem(BaseModel):
    id: int
    challenge_id: int
    user_id: int
    username: Optional[str] = None
    answer: str
    answer_2: Optional[str] = None
    content: Optional[str] = None
    likes_count: int = 0
    submitted_at: dt.datetime

    class Config:
        from_attributes = True

class ChallengeResponseListResponse(BaseModel):
    items: List[ChallengeResponseItem]
    total: int
    page: int
    page_size: int

class ChallengeHistoryItem(BaseModel):
    id: int
    challenge_id: int
    challenge_type: Optional[str] = "fill_blank"
    answer: str
    answer_2: Optional[str] = None
    content: Optional[str] = None
    exp_gained: int = 0
    points_gained: int = 0
    ai_score: int = 0
    beauty_score: int = 0
    creativity_score: int = 0
    mood_score: int = 0
    submitted_at: dt.datetime

    class Config:
        from_attributes = True

class ChallengeHistoryResponse(BaseModel):
    items: List[ChallengeHistoryItem]
    total: int
    streak_days: int
    page: int
    page_size: int

class ChallengeDeleteResponse(BaseModel):
    id: int
    exp_deducted: int
    points_deducted: int
    message: str

class ChallengeRankingItem(BaseModel):
    rank: int
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    total_submissions: int
    total_exp: int
    total_points: int
    level: int
    exp: int

class ChallengeRankingResponse(BaseModel):
    items: List[ChallengeRankingItem]
    total: int
    period: str


class ChallengeAIGenerateRequest(BaseModel):
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    theme: Optional[str] = None
    dynasty: Optional[str] = None


class ChallengeAIGenerateResponse(BaseModel):
    sentence_template: str
    sentence_template_2: Optional[str] = None
    blank_count: int = 1
    original_answer: str
    original_answer_2: Optional[str] = None
    theme: Optional[str] = None
    mood: Optional[str] = None
    hint: Optional[str] = None
    difficulty: str = "medium"
    poem_title: Optional[str] = None
    poem_author: Optional[str] = None
    poem_dynasty: Optional[str] = None


class ChallengeAIHintRequest(BaseModel):
    hint_level: int = Field(1, ge=1, le=3)


class ChallengeAIHintResponse(BaseModel):
    hint_text: str
    hint_level: int
    next_available: bool


class ChallengeAIReviewResponse(BaseModel):
    best_answer_index: int = 0
    best_reason: str = ""
    answer_tags: List[str] = []
    overall_review: str = ""
    diversity_note: str = ""


class ChallengeAICheckRequest(BaseModel):
    sentence_template: str = Field(..., min_length=2, max_length=200)
    sentence_template_2: Optional[str] = None
    user_answer: Optional[str] = None


class ChallengeAICheckResponse(BaseModel):
    is_valid: bool
    feedback: str
    suggestions: List[str] = []


class ChallengeAIExplainRecommendation(BaseModel):
    title: str = ""
    author: str = ""
    reason: str = ""


class ChallengeAIExplainResponse(BaseModel):
    poem_title: str = ""
    poem_author: str = ""
    poem_dynasty: str = ""
    poem_content: str = ""
    appreciation: str = ""
    word_analysis: str = ""
    comparison: str = ""
    recommendations: List[ChallengeAIExplainRecommendation] = []

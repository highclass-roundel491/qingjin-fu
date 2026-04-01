from typing import Optional
from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    system_prompt: Optional[str] = Field(None, max_length=2000)
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2048, ge=1, le=8192)


class AIChatResponse(BaseModel):
    content: str
    model: str


class AIScoreRequest(BaseModel):
    question: str = Field(..., min_length=1)
    correct_answers: list[str] = Field(..., min_length=1)
    user_answer: str = Field(..., min_length=1)


class AIScoreResponse(BaseModel):
    score: int
    accuracy_score: int
    artistic_score: int
    diction_score: int
    feedback: str
    is_correct: bool


class AIReferencePoemInfo(BaseModel):
    title: str = Field(..., max_length=200)
    author: str = Field(..., max_length=100)
    dynasty: str = Field(..., max_length=50)
    content: str = Field(..., max_length=5000)
    genre: Optional[str] = None


class AICreationRequest(BaseModel):
    context: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field("continue", pattern="^(continue|inspire|generate|theme|imitate_guide)$")
    keywords: Optional[list[str]] = None
    reference_poem: Optional[AIReferencePoemInfo] = None


class AICreationResponse(BaseModel):
    content: str
    explanation: str
    suggestions: Optional[list[str]] = None


class AICheckPoemRequest(BaseModel):
    poem_text: str = Field(..., min_length=1, max_length=2000)


class AICheckPoemResponse(BaseModel):
    is_valid: bool
    tone_analysis: Optional[list] = None
    rhyme_analysis: Optional[dict] = None
    couplet_analysis: Optional[dict] = None
    issues: list = Field(default_factory=list)
    suggestions: list = Field(default_factory=list)


class AIAnalyzePoemRequest(BaseModel):
    poem_text: str = Field(..., min_length=1, max_length=2000)


class AIAnalyzePoemResponse(BaseModel):
    total_score: int
    meter_score: int
    artistic_score: int
    diction_score: int
    overall_score: int
    highlights: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    appreciation: str


class AIFeihuaRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=4)
    used_poems: list[str] = Field(default_factory=list)


class AIFeihuaResponse(BaseModel):
    verse: str
    poem_title: str
    author: str
    dynasty: str
    confidence: float


class AIPoemContextRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    dynasty: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=5000)
    genre: Optional[str] = None
    category: Optional[str] = None
    query_type: str = Field(
        ...,
        pattern="^(author_bio|deep_appreciation|allusions|verse_analysis|free_qa|meter_analysis)$",
    )
    question: Optional[str] = Field(None, max_length=500)


class AIPoemContextResponse(BaseModel):
    query_type: str
    content: str
    title: Optional[str] = None
    sections: Optional[list[dict]] = None
    lines: Optional[list[dict]] = None
    rhyme_scheme: Optional[str] = None
    meter_type: Optional[str] = None


class AIPoemChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class AIPoemChatRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    dynasty: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=5000)
    genre: Optional[str] = None
    category: Optional[str] = None
    history: list[AIPoemChatMessage] = Field(default_factory=list, max_length=20)
    message: str = Field(..., min_length=1, max_length=500)


class AIPoemChatResponse(BaseModel):
    reply: str
    title: Optional[str] = None

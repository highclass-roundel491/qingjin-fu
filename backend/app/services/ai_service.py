from abc import ABC, abstractmethod
from typing import Optional, Union
from enum import Enum
from ..core.config import settings


class AIModelTier(str, Enum):
    FLASH = "flash"
    PLUS = "plus"
    MAX = "max"


MODEL_NAME_MAP = {
    AIModelTier.FLASH: "qwen3.5-flash",
    AIModelTier.PLUS: "qwen3.5-plus",
    AIModelTier.MAX: "qwen3-max",
}


def resolve_model_tier(
    value: Optional[Union[str, AIModelTier]],
    fallback: AIModelTier = AIModelTier.PLUS,
) -> AIModelTier:
    if isinstance(value, AIModelTier):
        return value

    normalized = str(value or "").strip().lower()
    aliases = {
        "flash": AIModelTier.FLASH,
        "qwen-flash": AIModelTier.FLASH,
        "qwen3.5-flash": AIModelTier.FLASH,
        "plus": AIModelTier.PLUS,
        "qwen-plus": AIModelTier.PLUS,
        "qwen3.5-plus": AIModelTier.PLUS,
        "max": AIModelTier.MAX,
        "qwen-max": AIModelTier.MAX,
        "qwen3-max": AIModelTier.MAX,
    }
    return aliases.get(normalized, fallback)


def get_default_model_tier() -> AIModelTier:
    return resolve_model_tier(settings.AI_DEFAULT_MODEL_TIER, AIModelTier.PLUS)


def get_model_name(model_tier: Optional[Union[str, AIModelTier]] = None) -> str:
    resolved_tier = resolve_model_tier(model_tier, get_default_model_tier())
    return MODEL_NAME_MAP[resolved_tier]


class AIService(ABC):

    @abstractmethod
    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
    ) -> str:
        pass

    @abstractmethod
    async def score_answer(
        self,
        question: str,
        correct_answers: list[str],
        user_answer: str,
        poem_context: Optional[dict] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def assist_creation(
        self,
        context: str,
        mode: str = "continue",
        keywords: Optional[list[str]] = None,
        reference_poems: Optional[list[dict]] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def check_poem(
        self,
        poem_text: str,
    ) -> dict:
        pass

    @abstractmethod
    async def analyze_poem(
        self,
        poem_text: str,
        poem_metadata: Optional[dict] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def feihualing_respond(
        self,
        keyword: str,
        used_poems: list[str],
        candidate_poems: Optional[list[dict]] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def score_challenge(
        self,
        sentence_template: str,
        sentence_template_2: Optional[str],
        user_answer: str,
        user_answer_2: Optional[str],
        challenge_type: str,
        theme: Optional[str] = None,
        mood: Optional[str] = None,
        poem_context: Optional[dict] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def generate_challenge(
        self,
        poem_text: str,
        poem_title: str,
        poem_author: str,
        poem_dynasty: str,
        difficulty: str = "medium",
        challenge_type: str = "fill_blank",
    ) -> dict:
        pass

    @abstractmethod
    async def challenge_hint(
        self,
        sentence_template: str,
        hint_level: int,
        theme: Optional[str] = None,
        mood: Optional[str] = None,
        poem_context: Optional[dict] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def review_responses(
        self,
        sentence_template: str,
        sentence_template_2: Optional[str],
        answers: list[dict],
        theme: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def check_challenge(
        self,
        sentence_template: str,
        sentence_template_2: Optional[str],
        user_answer: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def poem_context(
        self,
        title: str,
        author: str,
        dynasty: str,
        content: str,
        query_type: str,
        genre: Optional[str] = None,
        category: Optional[str] = None,
        question: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    async def poem_chat(
        self,
        title: str,
        author: str,
        dynasty: str,
        content: str,
        history: list[dict],
        message: str,
        genre: Optional[str] = None,
        category: Optional[str] = None,
    ) -> dict:
        pass


_ai_service_instance: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service_instance
    if _ai_service_instance is None:
        from .qwen_service import QwenAIService
        _ai_service_instance = QwenAIService()
    return _ai_service_instance

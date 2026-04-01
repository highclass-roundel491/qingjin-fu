import hashlib
import json
import logging
from typing import Optional

from ..core.redis_cache import cache_get, cache_set

logger = logging.getLogger("uvicorn.error")

_DEFAULT_TTL = 3600 * 6


class LLMCache:

    @staticmethod
    def _make_key(prefix: str, **kwargs) -> str:
        raw = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
        h = hashlib.md5(raw.encode()).hexdigest()[:16]
        return f"llm:{prefix}:{h}"

    async def get(self, key: str) -> Optional[any]:
        return await cache_get(key)

    async def set(self, key: str, value: any, ttl: Optional[int] = None):
        await cache_set(key, value, ttl or _DEFAULT_TTL)


llm_cache = LLMCache()

CACHEABLE_QUERY_TYPES = {
    "author_bio": 3600 * 24,
    "meter_analysis": 3600 * 24,
    "allusions": 3600 * 12,
    "deep_appreciation": 3600 * 12,
    "verse_analysis": 3600 * 12,
    "check_poem": 3600 * 24,
    "analyze_poem": 3600 * 12,
}

from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import AgentEngine
from ..tool_router import get_tools_for_skill
from ..prompts.poem_prompts import ANALYZE_SYSTEM_PROMPT
from ..cache import llm_cache, CACHEABLE_QUERY_TYPES, LLMCache
from ...services.ai_service import AIModelTier
import logging
from typing import Optional, Callable

logger = logging.getLogger("uvicorn.error")


async def agent_analyze_poem(
    engine: AgentEngine,
    poem_text: str,
    db: AsyncSession,
    on_progress: Optional[Callable] = None,
) -> dict:
    cache_ttl = CACHEABLE_QUERY_TYPES.get("analyze_poem")
    if cache_ttl:
        cache_key = LLMCache._make_key("analyze_poem", poem_text=poem_text)
        cached = await llm_cache.get(cache_key)
        if cached is not None:
            logger.info(f"LLM 缓存命中: analyze_poem")
            return cached

    prompt = "请赏析以下诗词：\n\n"
    prompt += f"{poem_text}\n"
    prompt += "\n请先用工具查找这首诗的完整信息（标题、作者、背景等），然后再进行赏析。"
    prompt += "\n如需引用同作者或同题材的其他作品进行比较，也请先用工具查证。"

    result = await engine.run_agent_rewoo_json(
        prompt=prompt,
        system_prompt=ANALYZE_SYSTEM_PROMPT,
        db=db,
        temperature=0.5,
        max_tokens=2048,
        model_tier=AIModelTier.PLUS,
        tools=get_tools_for_skill("analysis"),
        on_progress=on_progress,
    )

    if cache_ttl:
        await llm_cache.set(cache_key, result, ttl=cache_ttl)
        logger.info(f"LLM 缓存写入: analyze_poem, TTL={cache_ttl}s")

    return result

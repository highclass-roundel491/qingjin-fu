import logging
from typing import Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import AgentEngine
from ..tool_router import get_tools_for_skill
from ..prompts.poem_prompts import SCORE_SYSTEM_PROMPT, CHECK_SYSTEM_PROMPT
from ..prompts.challenge_prompts import CHALLENGE_CHECK_SYSTEM_PROMPT
from ..cache import llm_cache, CACHEABLE_QUERY_TYPES, LLMCache
from ...services.ai_service import AIModelTier

logger = logging.getLogger("uvicorn.error")


async def agent_score_answer(
    engine: AgentEngine,
    question: str,
    correct_answers: list[str],
    user_answer: str,
    db: AsyncSession,
    poem_context: Optional[dict] = None,
) -> dict:
    prompt = f"题目：{question}\n标准答案：{'、'.join(correct_answers)}\n用户答案：{user_answer}\n"
    if poem_context:
        if poem_context.get("title"):
            prompt += f"\n【诗词信息】\n诗名：{poem_context['title']}\n"
        if poem_context.get("author"):
            prompt += f"作者：{poem_context['author']}\n"
        if poem_context.get("dynasty"):
            prompt += f"朝代：{poem_context['dynasty']}\n"
        if poem_context.get("full_content"):
            prompt += f"全文：{poem_context['full_content']}\n"
    prompt += "\n请先用 verify_poem_line 验证用户答案是否为真实诗句，再进行评判。"

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=SCORE_SYSTEM_PROMPT,
        db=db,
        temperature=0.3,
        max_tokens=1024,
        model_tier=AIModelTier.FLASH,
        tools=get_tools_for_skill("score_answer"),
    )


async def agent_check_poem(
    engine: AgentEngine,
    poem_text: str,
    db: AsyncSession,
    on_progress: Optional[Callable] = None,
) -> dict:
    cache_ttl = CACHEABLE_QUERY_TYPES.get("check_poem")
    if cache_ttl:
        cache_key = LLMCache._make_key("check_poem", poem_text=poem_text)
        cached = await llm_cache.get(cache_key)
        if cached is not None:
            logger.info(f"LLM 缓存命中: check_poem")
            return cached

    prompt = f"请检查以下诗词的格律：\n\n{poem_text}"
    prompt += "\n\n请先用 search_poems 搜索是否有类似的经典诗词可作参考，再进行格律检查。"

    result = await engine.run_agent_rewoo_json(
        prompt=prompt,
        system_prompt=CHECK_SYSTEM_PROMPT,
        db=db,
        temperature=0.2,
        max_tokens=2048,
        model_tier=AIModelTier.PLUS,
        tools=get_tools_for_skill("check_poem"),
        on_progress=on_progress,
    )

    if cache_ttl:
        await llm_cache.set(cache_key, result, ttl=cache_ttl)
        logger.info(f"LLM 缓存写入: check_poem, TTL={cache_ttl}s")

    return result


async def agent_check_challenge(
    engine: AgentEngine,
    sentence_template: str,
    db: AsyncSession,
    sentence_template_2: Optional[str] = None,
    user_answer: Optional[str] = None,
) -> dict:
    if sentence_template_2:
        prompt = f"请检查以下填字对句题目：\n\n"
        prompt += f"上句：{sentence_template}\n"
        prompt += f"下句：{sentence_template_2}\n"
        if user_answer:
            prompt += f"\n出题者的答案：{user_answer}\n"
            completed_1 = sentence_template.replace("__", user_answer) if "__" in sentence_template else sentence_template
            completed_2 = sentence_template_2.replace("__", user_answer) if "__" in sentence_template_2 else sentence_template_2
            prompt += f"填入后上句：{completed_1}\n"
            prompt += f"填入后下句：{completed_2}\n"
        prompt += "\n请先用 verify_poem_line 验证题面是否为真实诗句，再检查：1)上下句是否对仗工整 2)平仄是否协调 3)挖空位置是否对应且合理 4)挖空的字是否是关键实词"
    else:
        prompt = f"请检查以下续写接力起始句：\n\n"
        prompt += f"起始句：{sentence_template}\n"
        prompt += "\n请先用 verify_poem_line 验证起始句是否为真实诗句，再检查：1)句子是否有诗意 2)是否适合作为起始句让他人续写 3)平仄是否自然 4)意象是否清晰"

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=CHALLENGE_CHECK_SYSTEM_PROMPT,
        db=db,
        temperature=0.3,
        max_tokens=1024,
        model_tier=AIModelTier.FLASH,
        tools=get_tools_for_skill("check_challenge"),
    )

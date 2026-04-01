import logging
import re
from typing import Optional, Callable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import AgentEngine
from ..prompts.poem_prompts import POEM_CONTEXT_PROMPTS
from ..cache import llm_cache, CACHEABLE_QUERY_TYPES, LLMCache
from ...services.ai_service import AIModelTier
from ...models.poem import Poem

logger = logging.getLogger("uvicorn.error")

_POEM_TEXT_CLEAN_PATTERN = re.compile(r"[，。！？；、：,.!?;:\s\n\r\t\"'“”‘’（）()\-—]")
_APPRECIATION_SECTION_HEADINGS = ["主题情感", "意象手法", "价值点睛"]


def _normalize_poem_text(value: str) -> str:
    return _POEM_TEXT_CLEAN_PATTERN.sub("", value or "")


def _trim_text(value: str, limit: int) -> str:
    return (value or "").strip()[:limit].strip()


def _split_appreciation_sections(value: str) -> list[str]:
    normalized = (value or "").replace("\r", "\n")
    paragraphs = [item.strip() for item in normalized.split("\n") if item.strip()]
    if len(paragraphs) >= 2:
        return paragraphs[:3]
    sentences = [item.strip() for item in re.split(r"(?<=[。！？；])", normalized) if item.strip()]
    if not sentences:
        return []
    sections = []
    current = ""
    for sentence in sentences:
        candidate = f"{current}{sentence}"
        if current and len(candidate) > 110 and len(sections) < 2:
            sections.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current.strip():
        sections.append(current.strip())
    return sections[:3]


async def _build_local_deep_appreciation(
    db: AsyncSession,
    title: str,
    author: str,
    content: str,
) -> Optional[dict]:
    normalized_input = _normalize_poem_text(content)
    result = await db.execute(
        select(Poem)
        .where(Poem.title == title, Poem.author == author)
        .limit(5)
    )
    poems = result.scalars().all()
    matched_poem = None
    for poem in poems:
        if not poem.appreciation:
            continue
        if _normalize_poem_text(poem.content) == normalized_input:
            matched_poem = poem
            break
        if matched_poem is None:
            matched_poem = poem
    if matched_poem is None:
        return None
    source_text = (matched_poem.appreciation or "").strip()
    background = (matched_poem.background or "").strip()
    if len(source_text) < 80:
        return None
    if background and len(source_text) < 220:
        source_text = f"{source_text}\n{background}"
    sections_text = _split_appreciation_sections(source_text)
    sections = [
        {
            "heading": _APPRECIATION_SECTION_HEADINGS[min(idx, len(_APPRECIATION_SECTION_HEADINGS) - 1)],
            "text": _trim_text(section, 110),
        }
        for idx, section in enumerate(sections_text)
        if section.strip()
    ]
    return {
        "title": f"《{title}》深度赏析",
        "content": _trim_text(source_text, 320),
        "sections": sections[:3],
    }


async def agent_poem_context(
    engine: AgentEngine,
    title: str,
    author: str,
    dynasty: str,
    content: str,
    query_type: str,
    db: AsyncSession,
    genre: Optional[str] = None,
    category: Optional[str] = None,
    question: Optional[str] = None,
    user_id: Optional[int] = None,
    on_progress: Optional[Callable] = None,
) -> dict:
    system_prompt = POEM_CONTEXT_PROMPTS.get(query_type)
    if not system_prompt:
        raise ValueError(f"未知的查询类型: {query_type}")

    cache_ttl = CACHEABLE_QUERY_TYPES.get(query_type)
    if cache_ttl:
        cache_key = LLMCache._make_key(
            "poem_context",
            title=title, author=author, query_type=query_type,
        )
        cached = await llm_cache.get(cache_key)
        if cached is not None:
            logger.info(f"LLM 缓存命中: {query_type} for {title}")
            return cached

    if query_type == "deep_appreciation":
        local_result = await _build_local_deep_appreciation(db, title, author, content)
        if local_result is not None:
            local_result["query_type"] = query_type
            if cache_ttl:
                await llm_cache.set(cache_key, local_result, ttl=cache_ttl)
                logger.info(f"本地赏析缓存写入: {title}, TTL={cache_ttl}s")
            return local_result

    prompt = f"【诗词信息】\n"
    prompt += f"题目：《{title}》\n"
    prompt += f"作者：{author}（{dynasty}）\n"
    if genre:
        prompt += f"体裁：{genre}\n"
    if category:
        prompt += f"题材：{category}\n"
    prompt += f"\n【原文】\n{content}\n"

    if query_type == "free_qa" and question:
        prompt += f"\n【学生提问】\n{question}\n"
        prompt += "\n请回答以上问题。如需引用其他诗词或诗人信息，请先用工具查证。"
        if user_id:
            prompt += f"\n当前用户ID为 {user_id}，可用 get_user_profile 了解用户水平以调整回答深度，用 get_user_learning_history 了解其学习偏好以推荐关联内容。"
    elif query_type == "author_bio":
        prompt += f"\n请为{dynasty}{author}撰写诗人小传。请先用 get_author_info 工具查询诗人档案，并用 search_poems 查看其代表作品。"
    elif query_type == "deep_appreciation":
        prompt += "\n请对这首诗词做深度赏析。如需引用同作者其他作品或相关诗人信息进行比较，请先用工具查证。"
    elif query_type == "allusions":
        prompt += "\n请解读这首诗词中的典故与意象。如涉及其他诗词出处，请用工具查证。"
    elif query_type == "verse_analysis":
        prompt += "\n请对这首诗词做逐句精析。"
    elif query_type == "meter_analysis":
        prompt += "\n请对这首诗词做格律分析，逐字标注平仄。"

    from ..tool_router import get_tools_for_skill

    tier = AIModelTier.FLASH if query_type in ("author_bio", "allusions", "deep_appreciation", "verse_analysis", "meter_analysis") else AIModelTier.PLUS
    max_tokens = 1792 if query_type == "deep_appreciation" else 3072 if query_type in ("verse_analysis", "meter_analysis") else 2048
    use_planner = query_type == "free_qa"
    skill_key = f"poem_context_{query_type}"
    use_tools = get_tools_for_skill(skill_key)
    enable_react = query_type != "deep_appreciation"
    temperature = 0.4 if query_type == "deep_appreciation" else 0.5

    result = await engine.run_agent_json(
        prompt=prompt,
        system_prompt=system_prompt,
        db=db,
        temperature=temperature,
        max_tokens=max_tokens,
        model_tier=tier,
        tools=use_tools,
        enable_react=enable_react,
        enable_planner=use_planner,
        on_progress=on_progress,
    )

    result["query_type"] = query_type
    if "title" not in result:
        result["title"] = title
    if "content" not in result:
        result["content"] = ""

    if cache_ttl:
        await llm_cache.set(cache_key, result, ttl=cache_ttl)
        logger.info(f"LLM 缓存写入: {query_type} for {title}, TTL={cache_ttl}s")

    return result

from typing import Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import AgentEngine
from ..tool_router import get_tools_for_skill
from ..prompts.creation_prompts import CREATION_SYSTEM_PROMPT, INSPIRE_SYSTEM_PROMPT, IMITATE_GUIDE_SYSTEM_PROMPT, IMITATE_CREATION_CONTEXT
from ...services.ai_service import AIModelTier


async def agent_assist_creation(
    engine: AgentEngine,
    context: str,
    mode: str,
    db: AsyncSession,
    keywords: Optional[list[str]] = None,
    reference_poem: Optional[dict] = None,
    user_id: Optional[int] = None,
    on_progress: Optional[Callable] = None,
) -> dict:
    if mode == "imitate_guide":
        return await _imitate_guide(engine, db, reference_poem)

    if mode == "inspire":
        return await _inspire(engine, context, keywords, on_progress=on_progress)

    prompt = f"创作模式：{mode}\n上下文/主题：{context}"
    if keywords:
        prompt += f"\n关键词：{'、'.join(keywords)}"

    if reference_poem:
        ref_context = IMITATE_CREATION_CONTEXT.format(
            title=reference_poem.get("title", ""),
            dynasty=reference_poem.get("dynasty", ""),
            author=reference_poem.get("author", ""),
            genre=reference_poem.get("genre", "未知"),
            content=reference_poem.get("content", ""),
        )
        prompt = ref_context + "\n" + prompt

    if mode == "continue":
        prompt += "\n\n请参考当前内容的风格和主题来续写。如有需要可搜索相关经典诗词获取灵感。"
    elif mode in ("generate", "theme"):
        prompt += "\n\n请根据关键词进行创作，可搜索相关经典诗词作为参考。"

    if user_id:
        prompt += f"\n当前用户ID为 {user_id}。"

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=CREATION_SYSTEM_PROMPT,
        db=db,
        temperature=0.8,
        max_tokens=2048,
        model_tier=AIModelTier.PLUS,
        tools=get_tools_for_skill("creation"),
        enable_planner=True,
        on_progress=on_progress,
    )


async def _inspire(
    engine: AgentEngine,
    context: str,
    keywords: Optional[list[str]] = None,
    on_progress: Optional[Callable] = None,
) -> dict:
    prompt = f"主题：{context}"
    if keywords:
        prompt += f"\n关键词：{'、'.join(keywords)}"
    return await engine._call_json_completion(
        prompt=prompt,
        system_prompt=INSPIRE_SYSTEM_PROMPT,
        model_tier=AIModelTier.PLUS,
        temperature=0.85,
        max_tokens=1024,
        use_identity_guard=False,
        on_progress=on_progress,
    )


async def _imitate_guide(
    engine: AgentEngine,
    db: AsyncSession,
    reference_poem: Optional[dict],
) -> dict:
    if not reference_poem:
        return {
            "content": "请先选择一首参考诗词",
            "explanation": "未提供参考诗词",
            "suggestions": [],
        }

    prompt = (
        f"请分析以下诗词并提供仿写指导：\n\n"
        f"标题：{reference_poem.get('title', '')}\n"
        f"作者：〔{reference_poem.get('dynasty', '')}〕{reference_poem.get('author', '')}\n"
        f"体裁：{reference_poem.get('genre', '未知')}\n"
        f"原文：\n{reference_poem.get('content', '')}\n\n"
        f"请先用 get_poem_detail 或 search_poems 查找这首诗的详细信息，"
        f"再用 get_related_poems 查找同作者或同风格的其他作品作为对比参考，"
        f"最后给出详细的仿写指导。"
    )

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=IMITATE_GUIDE_SYSTEM_PROMPT,
        db=db,
        temperature=0.6,
        max_tokens=2048,
        model_tier=AIModelTier.PLUS,
        tools=get_tools_for_skill("creation_imitate"),
        enable_planner=True,
    )

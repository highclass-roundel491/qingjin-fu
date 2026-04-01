import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import AgentEngine
from ..prompts.poem_prompts import POEM_CHAT_SYSTEM_PROMPT
from ...services.ai_service import AIModelTier

logger = logging.getLogger("uvicorn.error")


async def agent_poem_chat(
    engine: AgentEngine,
    title: str,
    author: str,
    dynasty: str,
    content: str,
    history: list[dict],
    message: str,
    db: AsyncSession,
    genre: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[int] = None,
) -> dict:
    poem_info = f"【当前诗词】\n题目：《{title}》\n作者：{author}（{dynasty}）\n"
    if genre:
        poem_info += f"体裁：{genre}\n"
    if category:
        poem_info += f"题材：{category}\n"
    poem_info += f"\n【原文】\n{content}"

    system_prompt = POEM_CHAT_SYSTEM_PROMPT + "\n\n" + poem_info
    if user_id:
        system_prompt += f"\n\n当前用户ID为 {user_id}。如需个性化回答，可用 get_user_profile 了解用户水平，用 get_user_learning_history 了解其学习记录。"

    messages = []
    for h in history[-16:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        reply = await engine.run_agent_chat(
            messages_history=messages,
            system_prompt=system_prompt,
            db=db,
            temperature=0.6,
            max_tokens=1024,
            model_tier=AIModelTier.PLUS,
        )
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Agent对话失败: {e}")
        raise


async def agent_poem_chat_stream(
    engine: AgentEngine,
    title: str,
    author: str,
    dynasty: str,
    content: str,
    history: list[dict],
    message: str,
    db: AsyncSession,
    genre: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[int] = None,
    memory_context: Optional[str] = None,
):
    from ..tool_router import get_tools_for_skill

    poem_info = f"【当前诗词】\n题目：《{title}》\n作者：{author}（{dynasty}）\n"
    if genre:
        poem_info += f"体裁：{genre}\n"
    if category:
        poem_info += f"题材：{category}\n"
    poem_info += f"\n【原文】\n{content}"

    system_prompt = POEM_CHAT_SYSTEM_PROMPT + "\n\n" + poem_info
    if user_id:
        system_prompt += f"\n\n当前用户ID为 {user_id}。如需个性化回答，可用 get_user_profile 了解用户水平，用 get_user_learning_history 了解其学习记录。"
    if memory_context:
        system_prompt += "\n\n" + memory_context

    messages = []
    for h in history[-16:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    tools = get_tools_for_skill("poem_chat")

    async for chunk in engine.run_agent_chat_stream(
        messages_history=messages,
        system_prompt=system_prompt,
        db=db,
        temperature=0.6,
        max_tokens=1024,
        model_tier=AIModelTier.PLUS,
        tools=tools,
    ):
        yield chunk

from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import AgentEngine
from ..tool_router import get_tools_for_skill
from ..prompts.creation_prompts import FEIHUALING_SYSTEM_PROMPT
from ...services.ai_service import AIModelTier


async def agent_feihualing_respond(
    engine: AgentEngine,
    keyword: str,
    used_poems: list[str],
    db: AsyncSession,
) -> dict:
    used_text = "\n".join(f"- {p}" for p in used_poems) if used_poems else "（暂无）"
    prompt = f"令字：{keyword}\n已使用诗句：\n{used_text}\n"
    prompt += "\n优先用 search_poems 查找候选，再用 verify_poem_line 验证。"
    prompt += "\n若本地诗词库没有合适结果，也可直接返回其他真实诗句。"
    prompt += "\n若出处信息不确定，对应字段返回 null。"

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=FEIHUALING_SYSTEM_PROMPT,
        db=db,
        temperature=0.9,
        max_tokens=256,
        model_tier=AIModelTier.FLASH,
        tools=get_tools_for_skill("feihualing"),
    )

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import AgentEngine
from ..tool_router import get_tools_for_skill
from ..prompts.challenge_prompts import (
    CHALLENGE_SCORE_SYSTEM_PROMPT,
    CHALLENGE_GENERATE_SYSTEM_PROMPT,
    CHALLENGE_HINT_SYSTEM_PROMPT,
    REVIEW_RESPONSES_SYSTEM_PROMPT,
)
from ...services.ai_service import AIModelTier


CHALLENGE_EXPLAIN_SYSTEM_PROMPT = """你是「青衿赋」平台的翰林助手，负责在用户完成填字挑战后，提供诗词文化解读。

你的任务：
1. 找到题面所出自的原诗全文、作者与朝代
2. 解读原诗的意境与情感
3. 分析挖空字在原句中的用字妙处（炼字之妙）
4. 如果用户填的字与原字不同，对比两字的意境差异
5. 推荐 1-2 首相关的经典诗词供用户延伸学习

返回严格JSON：
- poem_title: 原诗标题
- poem_author: 原诗作者
- poem_dynasty: 朝代
- poem_content: 原诗全文
- appreciation: 原诗赏析（80字以内）
- word_analysis: 炼字分析（60字以内，聚焦被挖空的字）
- comparison: 用户用字与原字的对比（50字以内；若一致则写"与原诗相合"）
- recommendations: 推荐延伸诗词列表，每项含 title、author、reason（一句话理由）"""


async def agent_score_challenge(
    engine: AgentEngine,
    sentence_template: str,
    sentence_template_2: Optional[str],
    user_answer: str,
    user_answer_2: Optional[str],
    challenge_type: str,
    db: AsyncSession,
    theme: Optional[str] = None,
    mood: Optional[str] = None,
) -> dict:
    prompt = f"题目类型：{challenge_type}\n"
    if challenge_type == "continue_line":
        prompt += f"起始句：{sentence_template}\n"
        prompt += f"用户续写：{user_answer}\n"
    else:
        prompt += f"题面上句：{sentence_template}\n"
        prompt += f"用户填入：{user_answer}\n"
        if sentence_template_2 and user_answer_2:
            prompt += f"题面下句：{sentence_template_2}\n"
            prompt += f"用户填入：{user_answer_2}\n"
    if theme:
        prompt += f"题目主题：{theme}\n"
    if mood:
        prompt += f"情感氛围：{mood}\n"

    clean_text = sentence_template.replace("_", "")
    prompt += (
        f"\n请先用 verify_poem_line 验证「{clean_text}」是否为真实诗句，"
        f"如果能找到原诗，再用 get_poem_detail 获取全文作为评分参考。"
        f"\n然后根据原诗上下文进行评判。"
    )

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=CHALLENGE_SCORE_SYSTEM_PROMPT,
        db=db,
        temperature=0.3,
        max_tokens=1024,
        model_tier=AIModelTier.FLASH,
        tools=get_tools_for_skill("challenge_score"),
        enable_react=True,
    )


async def agent_generate_challenge(
    engine: AgentEngine,
    db: AsyncSession,
    difficulty: str = "medium",
    theme: Optional[str] = None,
    dynasty: Optional[str] = None,
) -> dict:
    prompt = f"请生成一道{difficulty}难度的填字挑战题目。\n"
    if theme:
        prompt += f"题目主题：{theme}\n"
    if dynasty:
        prompt += f"朝代偏好：{dynasty}\n"

    prompt += (
        "\n请先用 search_poems 搜索符合条件的经典诗词，"
        "从中选择一首适合出题的，"
        "再用 get_poem_detail 获取全文，"
        "然后从中选取对仗工整的上下句，各挖空一个关键字生成题目。"
        "\n生成后请用 verify_poem_line 验证题面的真实性。"
    )

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=CHALLENGE_GENERATE_SYSTEM_PROMPT,
        db=db,
        temperature=0.7,
        max_tokens=1024,
        model_tier=AIModelTier.PLUS,
        tools=get_tools_for_skill("challenge_generate"),
        enable_react=True,
        enable_planner=True,
    )


async def agent_challenge_hint(
    engine: AgentEngine,
    sentence_template: str,
    hint_level: int,
    db: AsyncSession,
    theme: Optional[str] = None,
    mood: Optional[str] = None,
) -> dict:
    prompt = f"题面：{sentence_template}\n"
    prompt += f"请给出第{hint_level}层提示。\n"
    if theme:
        prompt += f"题目主题：{theme}\n"
    if mood:
        prompt += f"情感氛围：{mood}\n"

    clean_text = sentence_template.replace("_", "")
    prompt += (
        f"\n请先用 verify_poem_line 或 search_poems 查找「{clean_text}」的出处，"
        f"找到原诗后根据原诗上下文给出层级化提示，但不要直接透露答案。"
    )

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=CHALLENGE_HINT_SYSTEM_PROMPT,
        db=db,
        temperature=0.5,
        max_tokens=512,
        model_tier=AIModelTier.FLASH,
        tools=get_tools_for_skill("challenge_hint"),
        enable_react=True,
    )


async def agent_review_responses(
    engine: AgentEngine,
    sentence_template: str,
    sentence_template_2: Optional[str],
    answers: list[dict],
    db: AsyncSession,
    theme: Optional[str] = None,
    original_answer: Optional[str] = None,
    original_answer_2: Optional[str] = None,
) -> dict:
    prompt = f"题面上句：{sentence_template}\n"
    if sentence_template_2:
        prompt += f"题面下句：{sentence_template_2}\n"
    if theme:
        prompt += f"题目主题：{theme}\n"
    if original_answer:
        prompt += f"标准上联答案：{original_answer}\n"
    if original_answer_2:
        prompt += f"标准下联答案：{original_answer_2}\n"
    prompt += f"\n共收到 {len(answers)} 位答题者的回答：\n"
    for i, a in enumerate(answers[:10]):
        prompt += f"\n答案{i}: {a.get('answer', '')}"
        if a.get('answer_2'):
            prompt += f" / {a['answer_2']}"
        if a.get('username'):
            prompt += f"（{a['username']}）"

    prompt += "\n\n请结合题面与标准答案进行横向赏析。"

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=REVIEW_RESPONSES_SYSTEM_PROMPT,
        db=db,
        temperature=0.6,
        max_tokens=1024,
        model_tier=AIModelTier.FLASH,
        tools=[],
        enable_react=False,
    )


async def agent_explain_challenge(
    engine: AgentEngine,
    sentence_template: str,
    sentence_template_2: Optional[str],
    user_answer: str,
    user_answer_2: Optional[str],
    original_answer: Optional[str],
    original_answer_2: Optional[str],
    db: AsyncSession,
    theme: Optional[str] = None,
) -> dict:
    prompt = f"题面上句：{sentence_template}\n"
    if sentence_template_2:
        prompt += f"题面下句：{sentence_template_2}\n"
    prompt += f"用户填入：{user_answer}\n"
    if user_answer_2:
        prompt += f"用户下联填入：{user_answer_2}\n"
    if original_answer:
        prompt += f"原始答案：{original_answer}\n"
    if original_answer_2:
        prompt += f"原始下联答案：{original_answer_2}\n"
    if theme:
        prompt += f"题目主题：{theme}\n"

    clean_text = sentence_template.replace("_", "")
    prompt += (
        f"\n请先用 verify_poem_line 或 search_poems 查找「{clean_text}」的出处，"
        f"找到原诗后用 get_poem_detail 获取全文，"
        f"再用 get_related_poems 推荐相关延伸诗词。"
        f"\n最后进行炼字分析和意境解读。"
    )

    return await engine.run_agent_json(
        prompt=prompt,
        system_prompt=CHALLENGE_EXPLAIN_SYSTEM_PROMPT,
        db=db,
        temperature=0.5,
        max_tokens=2048,
        model_tier=AIModelTier.PLUS,
        tools=get_tools_for_skill("challenge_explain"),
        enable_react=True,
        enable_planner=True,
    )

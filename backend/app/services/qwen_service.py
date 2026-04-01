import json
import logging
import re
from typing import Optional

from openai import AsyncOpenAI

from ..core.config import settings
from .ai_service import AIService, AIModelTier, get_default_model_tier, get_model_name

_SENSITIVE_PATTERN = re.compile(
    r"(dashscope|qwen|openai|anthropic|claude|deepseek|glm|zhipu|bailian|api[_-]?key)",
    re.IGNORECASE,
)


def _sanitize_error(e: Exception) -> str:
    msg = str(e)
    if _SENSITIVE_PATTERN.search(msg):
        return "AI服务暂时不可用，请稍后再试"
    return msg

from ..agent.prompts import (
    AI_IDENTITY_GUARD,
    AI_IDENTITY_GUARD_LITE,
    SCORE_SYSTEM_PROMPT,
    CREATION_SYSTEM_PROMPT,
    CHECK_SYSTEM_PROMPT,
    ANALYZE_SYSTEM_PROMPT,
    FEIHUALING_SYSTEM_PROMPT,
    POEM_CONTEXT_PROMPTS,
    POEM_CHAT_SYSTEM_PROMPT,
    CHALLENGE_SCORE_SYSTEM_PROMPT,
    CHALLENGE_GENERATE_SYSTEM_PROMPT,
    CHALLENGE_HINT_SYSTEM_PROMPT,
    CHALLENGE_CHECK_SYSTEM_PROMPT,
    REVIEW_RESPONSES_SYSTEM_PROMPT,
)
from ..agent.engine import AgentEngine
from ..agent.skills import (
    agent_poem_context as _skill_poem_context,
    agent_poem_chat as _skill_poem_chat,
    agent_feihualing_respond as _skill_feihualing,
    agent_assist_creation as _skill_creation,
    agent_analyze_poem as _skill_analyze,
    agent_poem_chat_stream as _skill_poem_chat_stream,
    agent_score_answer as _skill_score_answer,
    agent_check_poem as _skill_check_poem,
    agent_check_challenge as _skill_check_challenge,
)

logger = logging.getLogger("uvicorn.error")
AI_CONFIG_ERROR = "AI服务未配置，请先配置密钥后再试"
FEIHUALING_PROMPT_CANDIDATE_LIMIT = 8


class _UnavailableCompletions:
    def __init__(self, message: str):
        self.message = message

    async def create(self, *args, **kwargs):
        raise RuntimeError(self.message)


class _UnavailableChat:
    def __init__(self, message: str):
        self.completions = _UnavailableCompletions(message)


class _UnavailableClient:
    def __init__(self, message: str):
        self.chat = _UnavailableChat(message)


class QwenAIService(AIService):

    def __init__(self):
        api_key = (settings.DASHSCOPE_API_KEY or "").strip()
        timeout_seconds = getattr(settings, "AI_REQUEST_TIMEOUT_SECONDS", 60.0)
        max_retries = getattr(settings, "AI_MAX_RETRIES", 2)
        self._configured = bool(api_key)
        if self._configured:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                timeout=timeout_seconds,
                max_retries=max_retries,
            )
        else:
            logger.error("AI服务未配置：DASHSCOPE_API_KEY 为空")
            self.client = _UnavailableClient(AI_CONFIG_ERROR)
        self.agent = AgentEngine(self.client)

    def _get_model(self, tier: AIModelTier) -> str:
        return get_model_name(tier)

    def _ensure_configured(self):
        if not self._configured:
            raise RuntimeError(AI_CONFIG_ERROR)

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
        response_format: Optional[dict] = None,
        lite_guard: bool = False,
    ) -> str:
        self._ensure_configured()
        guard = AI_IDENTITY_GUARD_LITE if lite_guard else AI_IDENTITY_GUARD
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": guard + "\n" + system_prompt})
        else:
            messages.append({"role": "system", "content": guard})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self._get_model(model_tier),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI调用失败: {e}")
            raise RuntimeError(_sanitize_error(e)) from None

    async def _call_llm_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
        lite_guard: bool = False,
    ) -> dict:
        raw = await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_tier=model_tier,
            response_format={"type": "json_object"},
            lite_guard=lite_guard,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)

    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model_tier: AIModelTier = get_default_model_tier(),
    ) -> str:
        return await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_tier=model_tier,
        )

    async def score_answer(
        self,
        question: str,
        correct_answers: list[str],
        user_answer: str,
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
        prompt += "\n请评判该答案。"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=SCORE_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1024,
            model_tier=AIModelTier.FLASH,
            lite_guard=True,
        )

    async def assist_creation(
        self,
        context: str,
        mode: str = "continue",
        keywords: Optional[list[str]] = None,
        reference_poems: Optional[list[dict]] = None,
    ) -> dict:
        prompt = f"创作模式：{mode}\n上下文/主题：{context}"
        if keywords:
            prompt += f"\n关键词：{'、'.join(keywords)}"
        if reference_poems:
            prompt += "\n\n【参考诗词】\n"
            for p in reference_poems[:5]:
                prompt += f"- 《{p.get('title', '')}》{p.get('author', '')}：{p.get('content', '')}\n"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=CREATION_SYSTEM_PROMPT,
            temperature=0.8,
            max_tokens=2048,
            model_tier=AIModelTier.PLUS,
        )

    async def check_poem(
        self,
        poem_text: str,
    ) -> dict:
        prompt = f"请检查以下诗词的格律：\n\n{poem_text}"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=CHECK_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2048,
            model_tier=AIModelTier.PLUS,
        )

    async def analyze_poem(
        self,
        poem_text: str,
        poem_metadata: Optional[dict] = None,
    ) -> dict:
        prompt = "请赏析以下诗词：\n\n"
        if poem_metadata:
            if poem_metadata.get("title"):
                prompt += f"题目：{poem_metadata['title']}\n"
            if poem_metadata.get("author"):
                prompt += f"作者：{poem_metadata['author']}（{poem_metadata.get('dynasty', '')}）\n"
            if poem_metadata.get("background"):
                prompt += f"创作背景：{poem_metadata['background']}\n"
        prompt += f"\n{poem_text}"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=ANALYZE_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=2048,
            model_tier=AIModelTier.PLUS,
        )

    async def feihualing_respond(
        self,
        keyword: str,
        used_poems: list[str],
        candidate_poems: Optional[list[dict]] = None,
    ) -> dict:
        used_text = "\n".join(f"- {p}" for p in used_poems) if used_poems else "（暂无）"
        prompt = f"令字：{keyword}\n已使用诗句：\n{used_text}\n"
        if candidate_poems:
            prompt += "\n可优先参考以下候选（不是完整范围）：\n"
            for idx, poem in enumerate(candidate_poems[:FEIHUALING_PROMPT_CANDIDATE_LIMIT], start=1):
                content = str(poem.get("content", "")).strip()
                if content:
                    prompt += f"{idx}. {content}\n"
        prompt += "\n若候选不合适，可直接给出其他真实诗句。若出处信息不确定，对应字段返回 null。"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=FEIHUALING_SYSTEM_PROMPT,
            temperature=0.9,
            max_tokens=256,
            model_tier=AIModelTier.FLASH,
            lite_guard=True,
        )

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
        prompt = f"题目类型：{challenge_type}\n"
        if challenge_type == "continue_line":
            prompt += f"起始句：{sentence_template}\n"
            prompt += f"用户续写：{user_answer}\n"
        else:
            completed = sentence_template.replace("__", user_answer) if "__" in sentence_template else user_answer
            prompt += f"题面上句：{sentence_template}\n"
            prompt += f"用户填入：{user_answer}\n"
            prompt += f"完成句：{completed}\n"
            if sentence_template_2 and user_answer_2:
                completed_2 = sentence_template_2.replace("__", user_answer_2)
                prompt += f"题面下句：{sentence_template_2}\n"
                prompt += f"用户填入：{user_answer_2}\n"
                prompt += f"完成句：{completed_2}\n"
        if theme:
            prompt += f"题目主题：{theme}\n"
        if mood:
            prompt += f"情感氛围：{mood}\n"
        if poem_context:
            prompt += "\n【原诗信息】\n"
            if poem_context.get("title"):
                prompt += f"诗名：{poem_context['title']}\n"
            if poem_context.get("author"):
                prompt += f"作者：{poem_context['author']}（{poem_context.get('dynasty', '')}）\n"
            if poem_context.get("original_answer"):
                prompt += f"原诗标准答案：{poem_context['original_answer']}\n"
            if poem_context.get("full_content"):
                prompt += f"全文：{poem_context['full_content']}\n"
        prompt += "\n请评判该填字。"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=CHALLENGE_SCORE_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1024,
            model_tier=AIModelTier.FLASH,
            lite_guard=True,
        )

    async def generate_challenge(
        self,
        poem_text: str,
        poem_title: str,
        poem_author: str,
        poem_dynasty: str,
        difficulty: str = "medium",
        challenge_type: str = "fill_blank",
    ) -> dict:
        prompt = f"请从以下诗词中生成一道{difficulty}难度的填字挑战题目。\n\n"
        prompt += f"诗名：《{poem_title}》\n"
        prompt += f"作者：{poem_author}（{poem_dynasty}）\n"
        prompt += f"全文：\n{poem_text}\n"
        prompt += f"\n挑战类型：{challenge_type}\n"
        prompt += f"难度：{difficulty}"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=CHALLENGE_GENERATE_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=1024,
            model_tier=AIModelTier.FLASH,
            lite_guard=True,
        )

    async def challenge_hint(
        self,
        sentence_template: str,
        hint_level: int,
        theme: Optional[str] = None,
        mood: Optional[str] = None,
        poem_context: Optional[dict] = None,
    ) -> dict:
        prompt = f"题面：{sentence_template}\n"
        prompt += f"请给出第{hint_level}层提示。\n"
        if theme:
            prompt += f"题目主题：{theme}\n"
        if mood:
            prompt += f"情感氛围：{mood}\n"
        if poem_context:
            prompt += "\n【原诗信息（仅供你参考，不要直接透露给学生）】\n"
            if poem_context.get("title"):
                prompt += f"诗名：{poem_context['title']}\n"
            if poem_context.get("author"):
                prompt += f"作者：{poem_context['author']}（{poem_context.get('dynasty', '')}）\n"
            if poem_context.get("original_answer"):
                prompt += f"标准答案：{poem_context['original_answer']}\n"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=CHALLENGE_HINT_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=512,
            model_tier=AIModelTier.FLASH,
            lite_guard=True,
        )

    async def review_responses(
        self,
        sentence_template: str,
        sentence_template_2: Optional[str],
        answers: list[dict],
        theme: Optional[str] = None,
    ) -> dict:
        prompt = f"题面上句：{sentence_template}\n"
        if sentence_template_2:
            prompt += f"题面下句：{sentence_template_2}\n"
        if theme:
            prompt += f"题目主题：{theme}\n"
        prompt += f"\n共收到 {len(answers)} 位答题者的回答：\n"
        for i, a in enumerate(answers[:10]):
            prompt += f"\n答案{i}: {a.get('answer', '')}"
            if a.get('answer_2'):
                prompt += f" / {a['answer_2']}"
            if a.get('username'):
                prompt += f"（{a['username']}）"
        prompt += "\n\n请进行横向赏析。"
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=REVIEW_RESPONSES_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=2048,
            model_tier=AIModelTier.PLUS,
        )

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
        system_prompt = POEM_CONTEXT_PROMPTS.get(query_type)
        if not system_prompt:
            raise ValueError(f"未知的查询类型: {query_type}")

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
            prompt += "\n请回答以上问题。"
        elif query_type == "author_bio":
            prompt += f"\n请为{dynasty}{author}撰写诗人小传。"
        elif query_type == "deep_appreciation":
            prompt += "\n请对这首诗词做深度赏析。"
        elif query_type == "allusions":
            prompt += "\n请解读这首诗词中的典故与意象。"
        elif query_type == "verse_analysis":
            prompt += "\n请对这首诗词做逐句精析。"
        elif query_type == "meter_analysis":
            prompt += "\n请对这首诗词做格律分析，逐字标注平仄。"

        tier = AIModelTier.FLASH if query_type in ("author_bio", "allusions") else AIModelTier.PLUS
        max_tokens = 3072 if query_type in ("verse_analysis", "deep_appreciation", "meter_analysis") else 2048

        result = await self._call_llm_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=max_tokens,
            model_tier=tier,
        )

        result["query_type"] = query_type
        if "title" not in result:
            result["title"] = title
        if "content" not in result:
            result["content"] = ""

        return result

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
        poem_info = f"【当前诗词】\n题目：《{title}》\n作者：{author}（{dynasty}）\n"
        if genre:
            poem_info += f"体裁：{genre}\n"
        if category:
            poem_info += f"题材：{category}\n"
        poem_info += f"\n【原文】\n{content}"

        system_prompt = AI_IDENTITY_GUARD + "\n" + POEM_CHAT_SYSTEM_PROMPT + "\n\n" + poem_info

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-16:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        kwargs = {
            "model": self._get_model(AIModelTier.PLUS),
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1024,
        }

        try:
            response = await self.client.chat.completions.create(**kwargs)
            reply = response.choices[0].message.content
            return {"reply": reply}
        except Exception as e:
            logger.error(f"AI对话失败: {e}")
            raise RuntimeError(_sanitize_error(e)) from None

    async def check_challenge(
        self,
        sentence_template: str,
        sentence_template_2: Optional[str],
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
            
            prompt += "\n请严格检查：1)上下句是否对仗工整 2)平仄是否协调 3)挖空位置是否对应且合理 4)挖空的字是否是关键实词"
        else:
            prompt = f"请检查以下续写接力起始句：\n\n"
            prompt += f"起始句：{sentence_template}\n"
            prompt += "\n请检查：1)句子是否有诗意 2)是否适合作为起始句让他人续写 3)平仄是否自然 4)意象是否清晰"
        
        return await self._call_llm_json(
            prompt=prompt,
            system_prompt=CHALLENGE_CHECK_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1024,
            model_tier=AIModelTier.PLUS,
            lite_guard=True,
        )

    async def agent_poem_context(self, title, author, dynasty, content, query_type, db, genre=None, category=None, question=None, user_id=None, on_progress=None) -> dict:
        self._ensure_configured()
        return await _skill_poem_context(self.agent, title, author, dynasty, content, query_type, db, genre=genre, category=category, question=question, user_id=user_id, on_progress=on_progress)

    async def agent_poem_chat(self, title, author, dynasty, content, history, message, db, genre=None, category=None, user_id=None) -> dict:
        self._ensure_configured()
        return await _skill_poem_chat(self.agent, title, author, dynasty, content, history, message, db, genre=genre, category=category, user_id=user_id)

    async def agent_feihualing_respond(self, keyword, used_poems, db) -> dict:
        self._ensure_configured()
        return await _skill_feihualing(self.agent, keyword, used_poems, db)

    async def agent_assist_creation(self, context, mode, db, keywords=None, reference_poem=None, user_id=None, on_progress=None) -> dict:
        self._ensure_configured()
        return await _skill_creation(self.agent, context, mode, db, keywords=keywords, reference_poem=reference_poem, user_id=user_id, on_progress=on_progress)

    async def agent_analyze_poem(self, poem_text, db, on_progress=None) -> dict:
        self._ensure_configured()
        return await _skill_analyze(self.agent, poem_text, db, on_progress=on_progress)

    async def agent_poem_chat_stream(self, title, author, dynasty, content, history, message, db, genre=None, category=None, user_id=None):
        self._ensure_configured()
        from ..agent.memory import AgentMemoryManager, enqueue_memory_extraction_event
        import json as _json

        memory_text = ""
        if user_id:
            try:
                memories = await AgentMemoryManager.load_memories(db, user_id)
                memory_text = AgentMemoryManager.format_memories_for_prompt(memories)
                if memory_text:
                    yield _json.dumps({"type": "memory", "content": f"已加载 {len(memories)} 条记忆"}, ensure_ascii=False)
            except Exception:
                pass

        async for chunk in _skill_poem_chat_stream(
            self.agent, title, author, dynasty, content, history, message, db,
            genre=genre, category=category, user_id=user_id, memory_context=memory_text,
        ):
            yield chunk

        if user_id and len(history) >= 2:
            try:
                all_msgs = [{"role": h["role"], "content": h["content"]} for h in history[-8:]]
                all_msgs.append({"role": "user", "content": message})
                await enqueue_memory_extraction_event(db, user_id, all_msgs, source="poem_chat_stream")
            except Exception:
                pass

    async def agent_score_answer(self, question, correct_answers, user_answer, db, poem_context=None) -> dict:
        self._ensure_configured()
        return await _skill_score_answer(self.agent, question, correct_answers, user_answer, db, poem_context=poem_context)

    async def agent_check_poem(self, poem_text, db, on_progress=None) -> dict:
        self._ensure_configured()
        return await _skill_check_poem(self.agent, poem_text, db, on_progress=on_progress)

    async def agent_check_challenge(self, sentence_template, db, sentence_template_2=None, user_answer=None) -> dict:
        self._ensure_configured()
        return await _skill_check_challenge(self.agent, sentence_template, db, sentence_template_2=sentence_template_2, user_answer=user_answer)

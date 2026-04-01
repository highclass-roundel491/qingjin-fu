import logging
from app.core.redis_cache import cache_get, cache_set
from app.services.ai_service import AIService

logger = logging.getLogger("uvicorn.error")

VERIFICATION_PROMPT = """你是古诗词鉴定专家。请判断以下诗句是否为真实的中国古典诗词。

诗句：{poem_content}
要求：必须包含「{keyword}」字

请从以下维度评估：
1. 是否为古典诗词风格（平仄、韵律、意境）
2. 是否包含指定关键字
3. 是否听起来像真实的古诗词（非现代仿作或网络段子）

返回JSON格式：
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "reason": "判断理由",
  "suggested_author": "可能的作者（如果能识别）",
  "suggested_dynasty": "可能的朝代"
}}"""


async def verify_poem_with_ai(
    poem_content: str,
    keyword: str,
    ai_service: AIService
) -> dict:
    import hashlib
    cache_key = f"poem_verify:{hashlib.sha256((poem_content + keyword).encode()).hexdigest()[:16]}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        prompt = VERIFICATION_PROMPT.format(
            poem_content=poem_content,
            keyword=keyword
        )
        result = await ai_service._call_llm_json(
            prompt=prompt,
            system_prompt="你是专业的古诗词鉴定专家，精通中国古典文学。",
            temperature=0.3,
            max_tokens=512,
            lite_guard=True
        )
        await cache_set(cache_key, result, ttl=86400)
        return result
    except Exception as e:
        logger.error(f"AI验证诗句失败: {e}")
        return {
            "is_valid": False,
            "confidence": 0.0,
            "reason": "AI验证服务暂时不可用"
        }

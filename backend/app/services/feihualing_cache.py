import logging
from sqlalchemy.ext.asyncio import AsyncSession
from .poem_search import search_poems_by_keyword

logger = logging.getLogger("uvicorn.error")

from app.core.config import FEIHUALING_COMMON_KEYWORDS


async def prewarm_feihualing_cache(db: AsyncSession):
    logger.info("开始预热飞花令缓存...")
    success_count = 0
    for keyword in FEIHUALING_COMMON_KEYWORDS:
        try:
            await search_poems_by_keyword(db, keyword, limit=80)
            success_count += 1
        except Exception as e:
            logger.warning(f"预热关键字 '{keyword}' 失败: {e}")
    logger.info(f"飞花令缓存预热完成，成功 {success_count}/{len(FEIHUALING_COMMON_KEYWORDS)} 个关键字")

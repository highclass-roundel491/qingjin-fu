import json
import random as _random
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.poem import Poem
from ...core.poet_data import get_dynasty_profile, POET_PROFILES

RANDOM_POEM_TOOL = {
    "type": "function",
    "function": {
        "name": "random_poem",
        "description": "从诗词库中随机获取一首诗词，可按朝代、题材、作者筛选。适用于灵感激发、随机推荐、游戏出题等场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "dynasty": {
                    "type": "string",
                    "description": "可选，限定朝代，如唐、宋"
                },
                "category": {
                    "type": "string",
                    "description": "可选，限定题材，如送别、边塞、山水田园"
                },
                "author": {
                    "type": "string",
                    "description": "可选，限定作者"
                }
            },
            "required": []
        }
    }
}

GET_DYNASTY_CONTEXT_TOOL = {
    "type": "function",
    "function": {
        "name": "get_dynasty_context",
        "description": "获取某个朝代的文学背景概况，包括文学特征、代表诗人、诗词数量分布。适用于讨论文学史、理解时代背景等场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "dynasty": {
                    "type": "string",
                    "description": "朝代名称，如唐、宋、元、明、清"
                }
            },
            "required": ["dynasty"]
        }
    }
}


def _apply_poem_filters(query, dynasty: Optional[str] = None, category: Optional[str] = None, author: Optional[str] = None):
    if dynasty:
        query = query.where(Poem.dynasty == dynasty)
    if category:
        query = query.where(Poem.category == category)
    if author:
        query = query.where(Poem.author == author)
    return query


async def tool_random_poem(
    db: AsyncSession,
    dynasty: Optional[str] = None,
    category: Optional[str] = None,
    author: Optional[str] = None,
) -> str:
    query = _apply_poem_filters(select(Poem), dynasty=dynasty, category=category, author=author)
    count_q = _apply_poem_filters(
        select(func.count()).select_from(Poem),
        dynasty=dynasty,
        category=category,
        author=author,
    )
    total = (await db.execute(count_q)).scalar() or 0
    if total == 0:
        return json.dumps({"error": "未找到符合条件的诗词"}, ensure_ascii=False)

    offset = _random.randint(0, total - 1)
    query = query.offset(offset).limit(1)
    result = await db.execute(query)
    poem = result.scalar_one_or_none()
    if not poem:
        return json.dumps({"error": "未找到符合条件的诗词"}, ensure_ascii=False)
    return json.dumps({
        "title": poem.title,
        "author": poem.author,
        "dynasty": poem.dynasty,
        "content": poem.content,
        "category": poem.category or "",
        "genre": poem.genre or "",
        "tags": poem.tags or "",
    }, ensure_ascii=False)


async def tool_get_dynasty_context(
    db: AsyncSession,
    dynasty: str,
) -> str:
    profile = get_dynasty_profile(dynasty)

    count_q = select(func.count()).select_from(Poem).where(Poem.dynasty == dynasty)
    count_r = await db.execute(count_q)
    total = count_r.scalar() or 0

    cat_q = (
        select(Poem.category, func.count().label("cnt"))
        .where(Poem.dynasty == dynasty)
        .group_by(Poem.category)
        .order_by(func.count().desc())
        .limit(10)
    )
    cat_r = await db.execute(cat_q)
    categories = [{"name": r[0] or "未分类", "count": r[1]} for r in cat_r.all()]

    top_q = (
        select(Poem.author, func.count().label("cnt"))
        .where(Poem.dynasty == dynasty)
        .group_by(Poem.author)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_r = await db.execute(top_q)
    top_authors = []
    for row in top_r.all():
        author_info = {"name": row[0], "poem_count": row[1]}
        p = POET_PROFILES.get(row[0])
        if p:
            author_info["alias"] = p.get("alias", "")
            author_info["styles"] = p.get("styles", [])
        top_authors.append(author_info)

    result = {
        "dynasty": dynasty,
        "total_poems": total,
        "top_authors": top_authors,
        "category_distribution": categories,
    }
    if profile:
        result["description"] = profile.get("description", "")
        result["influence"] = profile.get("influence", "")
        result["poem_count_label"] = profile.get("poem_count_label", "")

    return json.dumps(result, ensure_ascii=False)

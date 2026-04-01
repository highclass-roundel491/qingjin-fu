import json
from typing import Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.poem import Poem

SEARCH_POEMS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_poems",
        "description": "在诗词数据库中搜索诗词。可按关键词搜索诗句内容，也可按作者、朝代、题材筛选。返回匹配的诗词列表（标题、作者、朝代、内容摘要）。当你需要引用具体诗词、查找包含某个字/词的诗句、或寻找某位诗人的作品时，请使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，用于在诗句内容中检索"
                },
                "author": {
                    "type": "string",
                    "description": "按诗人姓名筛选"
                },
                "dynasty": {
                    "type": "string",
                    "description": "按朝代筛选，如唐、宋、元、明、清"
                },
                "category": {
                    "type": "string",
                    "description": "按题材筛选，如送别、边塞、山水田园、咏物、咏史怀古"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量上限，默认5",
                    "default": 5
                }
            },
            "required": []
        }
    }
}

GET_POEM_DETAIL_TOOL = {
    "type": "function",
    "function": {
        "name": "get_poem_detail",
        "description": "获取一首诗词的完整详细信息，包括原文全文、译文、注释、创作背景、鉴赏。当你需要深入分析一首具体的诗词时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "诗词标题"
                },
                "author": {
                    "type": "string",
                    "description": "诗词作者，用于辅助精确匹配"
                }
            },
            "required": ["title"]
        }
    }
}

VERIFY_POEM_LINE_TOOL = {
    "type": "function",
    "function": {
        "name": "verify_poem_line",
        "description": "验证一句诗是否真实存在于诗词数据库中，并返回其出处信息（诗名、作者、朝代、完整原文）。当你需要确认引用的诗句是否准确、或在飞花令等游戏中验证答案时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "line": {
                    "type": "string",
                    "description": "要验证的诗句内容"
                }
            },
            "required": ["line"]
        }
    }
}

GET_RELATED_POEMS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_related_poems",
        "description": "获取与指定诗词相关的其他诗词，可按同作者、同题材、或内容相似度查找。用于拓展分析、比较鉴赏、或推荐延伸阅读。",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "参考诗词的标题"
                },
                "author": {
                    "type": "string",
                    "description": "参考诗词的作者"
                },
                "relation_type": {
                    "type": "string",
                    "enum": ["same_author", "same_category", "similar_content"],
                    "description": "关联类型：same_author=同作者, same_category=同题材, similar_content=内容相似",
                    "default": "same_author"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量上限，默认5",
                    "default": 5
                }
            },
            "required": ["author"]
        }
    }
}


async def tool_search_poems(
    db: AsyncSession,
    keyword: Optional[str] = None,
    author: Optional[str] = None,
    dynasty: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 5,
) -> str:
    query = select(Poem)
    if keyword:
        query = query.where(
            or_(Poem.content.contains(keyword), Poem.title.contains(keyword))
        )
    if author:
        query = query.where(Poem.author == author)
    if dynasty:
        query = query.where(Poem.dynasty == dynasty)
    if category:
        query = query.where(Poem.category == category)
    query = query.limit(min(limit, 10))
    result = await db.execute(query)
    poems = result.scalars().all()
    if not poems:
        return json.dumps({"results": [], "message": "未找到匹配的诗词"}, ensure_ascii=False)
    items = []
    for p in poems:
        content_preview = p.content[:80] + "..." if len(p.content) > 80 else p.content
        items.append({
            "title": p.title,
            "author": p.author,
            "dynasty": p.dynasty,
            "content_preview": content_preview,
            "category": p.category or "",
            "genre": p.genre or "",
        })
    return json.dumps({"results": items, "total_found": len(items)}, ensure_ascii=False)


async def tool_get_poem_detail(
    db: AsyncSession,
    title: str,
    author: Optional[str] = None,
) -> str:
    query = select(Poem).where(Poem.title.contains(title))
    if author:
        query = query.where(Poem.author == author)
    query = query.limit(1)
    result = await db.execute(query)
    poem = result.scalar_one_or_none()
    if not poem:
        return json.dumps({"error": f"未找到标题含「{title}」的诗词"}, ensure_ascii=False)
    annotation = (poem.annotation or "")[:300]
    appreciation = (poem.appreciation or "")[:300]
    background = (poem.background or "")[:200]
    return json.dumps({
        "title": poem.title,
        "author": poem.author,
        "dynasty": poem.dynasty,
        "content": poem.content,
        "translation": poem.translation or "",
        "annotation": annotation,
        "background": background,
        "appreciation": appreciation,
        "category": poem.category or "",
        "genre": poem.genre or "",
    }, ensure_ascii=False)


async def tool_verify_poem_line(
    db: AsyncSession,
    line: str,
) -> str:
    clean = line.strip().rstrip("，。？！,.?!")
    if not clean:
        return json.dumps({"verified": False, "reason": "诗句为空"}, ensure_ascii=False)

    search_terms = [clean]
    if len(clean) > 10:
        search_terms.append(clean[:10])
        search_terms.append(clean[-10:])

    for term in search_terms:
        query = select(Poem).where(Poem.content.contains(term)).limit(5)
        result = await db.execute(query)
        poems = result.scalars().all()
        for poem in poems:
            if clean in poem.content:
                return json.dumps({
                    "verified": True,
                    "title": poem.title,
                    "author": poem.author,
                    "dynasty": poem.dynasty,
                    "full_content": poem.content[:200],
                }, ensure_ascii=False)

    return json.dumps({
        "verified": False,
        "reason": f"数据库中未找到包含「{clean[:15]}」的诗句，该诗句可能不存在或未收录",
    }, ensure_ascii=False)


async def tool_get_related_poems(
    db: AsyncSession,
    author: str,
    title: Optional[str] = None,
    relation_type: str = "same_author",
    limit: int = 5,
) -> str:
    query = select(Poem)
    if relation_type == "same_author":
        query = query.where(Poem.author == author)
        if title:
            query = query.where(Poem.title != title)
    elif relation_type == "same_category":
        if title:
            ref_q = select(Poem.category).where(Poem.title.contains(title)).limit(1)
            ref_r = await db.execute(ref_q)
            cat = ref_r.scalar_one_or_none()
            if cat:
                query = query.where(Poem.category == cat)
                query = query.where(Poem.title != title)
            else:
                return json.dumps({"results": [], "message": "未找到参考诗词"}, ensure_ascii=False)
        else:
            return json.dumps({"results": [], "message": "same_category 模式需要提供 title"}, ensure_ascii=False)
    elif relation_type == "similar_content":
        if title:
            ref_q = select(Poem.content).where(Poem.title.contains(title)).limit(1)
            ref_r = await db.execute(ref_q)
            content = ref_r.scalar_one_or_none()
            if content:
                query = query.where(Poem.content.contains(content[:10]))
                query = query.where(Poem.title != title)
            else:
                return json.dumps({"results": [], "message": "未找到参考诗词"}, ensure_ascii=False)

    query = query.limit(min(limit, 10))
    result = await db.execute(query)
    poems = result.scalars().all()

    items = []
    for p in poems:
        items.append({
            "title": p.title,
            "author": p.author,
            "dynasty": p.dynasty,
            "content_preview": p.content[:60],
            "category": p.category or "",
        })
    return json.dumps({"results": items, "relation_type": relation_type}, ensure_ascii=False)

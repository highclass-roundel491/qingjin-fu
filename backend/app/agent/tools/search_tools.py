import json
from typing import Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.poem import Poem

SEARCH_POEMS_ADVANCED_TOOL = {
    "type": "function",
    "function": {
        "name": "search_poems_advanced",
        "description": "高级诗词搜索：在标题、内容、注释、译文、标签中跨字段全文检索。比 search_poems 更强大，适用于模糊搜索、按意象搜索、按典故搜索等需要更广泛匹配的场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，将在标题、内容、注释、译文、标签中同时检索"
                },
                "keyword": {
                    "type": "string",
                    "description": "query 的兼容别名"
                },
                "dynasty": {
                    "type": "string",
                    "description": "可选，限定朝代"
                },
                "genre": {
                    "type": "string",
                    "description": "可选，限定体裁，如五言绝句、七言律诗、词"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量上限，默认5",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}


async def tool_search_poems_advanced(
    db: AsyncSession,
    query: Optional[str] = None,
    keyword: Optional[str] = None,
    dynasty: Optional[str] = None,
    genre: Optional[str] = None,
    limit: int = 5,
) -> str:
    search_text = (query or keyword or "").strip()
    if not search_text:
        return json.dumps({"results": [], "message": "搜索关键词不能为空"}, ensure_ascii=False)

    keyword = search_text
    cap = min(limit, 15)

    primary_stmt = select(Poem).where(
        or_(
            Poem.title.contains(keyword),
            Poem.content.contains(keyword),
        )
    )
    if dynasty:
        primary_stmt = primary_stmt.where(Poem.dynasty == dynasty)
    if genre:
        primary_stmt = primary_stmt.where(Poem.genre == genre)
    primary_stmt = primary_stmt.limit(cap)

    result = await db.execute(primary_stmt)
    poems = list(result.scalars().all())

    if len(poems) < cap:
        found_ids = {p.id for p in poems}
        fallback_stmt = select(Poem).where(
            and_(
                ~Poem.id.in_(found_ids) if found_ids else True,
                or_(
                    Poem.tags.contains(keyword),
                    Poem.annotation.contains(keyword),
                    Poem.translation.contains(keyword),
                )
            )
        )
        if dynasty:
            fallback_stmt = fallback_stmt.where(Poem.dynasty == dynasty)
        if genre:
            fallback_stmt = fallback_stmt.where(Poem.genre == genre)
        fallback_stmt = fallback_stmt.limit(cap - len(poems))
        fb_result = await db.execute(fallback_stmt)
        poems.extend(fb_result.scalars().all())

    if not poems:
        return json.dumps({"results": [], "message": f"未找到与「{keyword}」相关的诗词"}, ensure_ascii=False)

    items = []
    for p in poems:
        match_fields = []
        if keyword in (p.title or ""):
            match_fields.append("标题")
        if keyword in (p.content or ""):
            match_fields.append("正文")
        if keyword in (p.annotation or ""):
            match_fields.append("注释")
        if keyword in (p.translation or ""):
            match_fields.append("译文")
        if keyword in (p.tags or ""):
            match_fields.append("标签")
        if keyword in (p.appreciation or ""):
            match_fields.append("赏析")

        items.append({
            "title": p.title,
            "author": p.author,
            "dynasty": p.dynasty,
            "content_preview": p.content[:80] + "..." if len(p.content) > 80 else p.content,
            "category": p.category or "",
            "genre": p.genre or "",
            "match_in": match_fields,
        })

    return json.dumps({"results": items, "total_found": len(items), "query": keyword}, ensure_ascii=False)

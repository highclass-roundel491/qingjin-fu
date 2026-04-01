import json
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.poem import Poem

COUNT_POEMS_STATS_TOOL = {
    "type": "function",
    "function": {
        "name": "count_poems_stats",
        "description": "统计诗词库中的数据概况，如某朝代有多少首诗、某作者有多少首、某题材有多少首。用于回答关于诗词库数据量的问题。",
        "parameters": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "enum": ["dynasty", "author", "category"],
                    "description": "按什么维度统计"
                },
                "filter_value": {
                    "type": "string",
                    "description": "可选的筛选值，如指定朝代名或作者名"
                }
            },
            "required": ["group_by"]
        }
    }
}


async def tool_count_poems_stats(
    db: AsyncSession,
    group_by: str,
    filter_value: Optional[str] = None,
) -> str:
    col_map = {
        "dynasty": Poem.dynasty,
        "author": Poem.author,
        "category": Poem.category,
    }
    col = col_map.get(group_by)
    if not col:
        return json.dumps({"error": f"不支持的统计维度: {group_by}"}, ensure_ascii=False)

    query = select(col, func.count().label("count")).group_by(col)
    if filter_value:
        query = query.where(col == filter_value)
    query = query.order_by(func.count().desc()).limit(20)

    result = await db.execute(query)
    rows = result.all()

    stats = [{"name": r[0] or "未分类", "count": r[1]} for r in rows]
    total = sum(s["count"] for s in stats)
    return json.dumps({
        "group_by": group_by,
        "stats": stats,
        "total": total,
    }, ensure_ascii=False)

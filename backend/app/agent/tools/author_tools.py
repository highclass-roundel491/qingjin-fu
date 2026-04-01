import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.poem import Poem
from ...core.poet_data import get_poet_profile, get_poet_relations

GET_AUTHOR_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_author_info",
        "description": "获取诗人的详细档案信息，包括字号别称、生卒年、创作风格、文学地位描述、在库诗作数量与代表作、以及与其他诗人的关系。当你需要介绍或讨论某位诗人时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "author_name": {
                    "type": "string",
                    "description": "诗人姓名"
                }
            },
            "required": ["author_name"]
        }
    }
}


async def tool_get_author_info(
    db: AsyncSession,
    author_name: str,
) -> str:
    query = select(Poem).where(Poem.author == author_name)
    result = await db.execute(query)
    poems = result.scalars().all()

    profile = get_poet_profile(author_name)
    relations = get_poet_relations(author_name)

    if not poems and not profile:
        return json.dumps({"error": f"未找到诗人「{author_name}」的信息"}, ensure_ascii=False)

    categories = list(set((p.category or "其他") for p in poems)) if poems else []
    top_poems = sorted(poems, key=lambda p: (p.view_count or 0), reverse=True)[:5] if poems else []

    info = {
        "name": author_name,
        "poem_count": len(poems),
        "categories": categories,
        "representative_poems": [
            {"title": p.title, "content": p.content[:60]}
            for p in top_poems
        ],
    }
    if profile:
        info["alias"] = profile.get("alias", "")
        info["years"] = profile.get("years", "")
        info["influence"] = profile.get("influence", 0)
        info["styles"] = profile.get("styles", [])
        info["description"] = profile.get("description", "")
    if relations:
        info["relations"] = [
            {
                "related_poet": r["target"] if r["source"] == author_name else r["source"],
                "label": r["label"],
                "description": r["description"],
            }
            for r in relations[:5]
        ]
    if poems:
        dynasty_set = set(p.dynasty for p in poems)
        info["dynasty"] = list(dynasty_set)[0] if len(dynasty_set) == 1 else list(dynasty_set)

    return json.dumps(info, ensure_ascii=False)

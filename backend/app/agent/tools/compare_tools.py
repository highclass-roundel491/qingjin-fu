import json
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.poem import Poem
from ...core.poet_data import get_poet_profile, get_poet_relations, get_relation_label

COMPARE_POETS_TOOL = {
    "type": "function",
    "function": {
        "name": "compare_poets",
        "description": "对比两位诗人的创作风格、文学成就、代表作品及历史关系。适用于比较鉴赏、文学史讨论、诗风异同分析等场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "poet_a": {
                    "type": "string",
                    "description": "第一位诗人姓名"
                },
                "poet_b": {
                    "type": "string",
                    "description": "第二位诗人姓名"
                }
            },
            "required": ["poet_a", "poet_b"]
        }
    }
}


async def tool_compare_poets(
    db: AsyncSession,
    poet_a: str,
    poet_b: str,
) -> str:
    profile_a = get_poet_profile(poet_a)
    profile_b = get_poet_profile(poet_b)

    q_a = select(Poem).where(Poem.author == poet_a)
    q_b = select(Poem).where(Poem.author == poet_b)
    r_a = await db.execute(q_a)
    r_b = await db.execute(q_b)
    poems_a = r_a.scalars().all()
    poems_b = r_b.scalars().all()

    if not poems_a and not profile_a:
        return json.dumps({"error": f"未找到诗人「{poet_a}」的信息"}, ensure_ascii=False)
    if not poems_b and not profile_b:
        return json.dumps({"error": f"未找到诗人「{poet_b}」的信息"}, ensure_ascii=False)

    def build_poet_info(name, profile, poems):
        top = sorted(poems, key=lambda p: (p.view_count or 0), reverse=True)[:3]
        cats = list(set((p.category or "其他") for p in poems))
        dynasties = list(set(p.dynasty for p in poems))
        info = {
            "name": name,
            "dynasty": dynasties[0] if len(dynasties) == 1 else dynasties,
            "poem_count": len(poems),
            "categories": cats,
            "top_poems": [{"title": p.title, "preview": p.content[:50]} for p in top],
        }
        if profile:
            info["alias"] = profile.get("alias", "")
            info["years"] = profile.get("years", "")
            info["styles"] = profile.get("styles", [])
            info["influence"] = profile.get("influence", 0)
            info["description"] = profile.get("description", "")
        return info

    info_a = build_poet_info(poet_a, profile_a, poems_a)
    info_b = build_poet_info(poet_b, profile_b, poems_b)

    relation_label = get_relation_label(poet_a, poet_b)
    relations = []
    if relation_label:
        for r in get_poet_relations(poet_a):
            other = r["target"] if r["source"] == poet_a else r["source"]
            if other == poet_b:
                relations.append({
                    "label": r["label"],
                    "description": r["description"],
                })
                break

    result = {
        "poet_a": info_a,
        "poet_b": info_b,
        "relation": relations[0] if relations else None,
        "style_contrast": {
            "a_styles": info_a.get("styles", []),
            "b_styles": info_b.get("styles", []),
        },
    }
    return json.dumps(result, ensure_ascii=False)

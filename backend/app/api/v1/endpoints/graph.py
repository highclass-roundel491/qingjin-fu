import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional, List
from pydantic import BaseModel
from app.core.database import get_db, AsyncSessionLocal
from app.core.redis_cache import cache_get, cache_set
from app.models.poem import Poem
from app.models.poet_relation_cache import PoetRelationCache
from app.core.poet_data import (
    get_poet_profile, get_poet_relations, get_relation_label,
    get_dynasty_profile, POET_PROFILES, POET_RELATIONS, DYNASTY_PROFILES
)
from app.services.ai_service import get_ai_service, AIModelTier
from app.api.deps import get_current_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


class GraphNode(BaseModel):
    id: str
    name: str
    category: int
    value: int
    symbolSize: int
    dynasty: Optional[str] = None
    poem_count: Optional[int] = None
    representative_work: Optional[str] = None
    alias: Optional[str] = None
    influence: Optional[int] = None
    styles: Optional[List[str]] = None
    description: Optional[str] = None


class GraphLink(BaseModel):
    source: str
    target: str
    value: int
    label: Optional[str] = None
    description: Optional[str] = None


class GraphCategory(BaseModel):
    name: str


class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]
    categories: List[GraphCategory]


class PoetRelationItem(BaseModel):
    target: str
    label: str
    description: str


class DynastyProfileItem(BaseModel):
    name: str
    description: str
    influence: str
    poem_count_label: str


class AuthorDetail(BaseModel):
    name: str
    dynasty: str
    poem_count: int
    categories: List[str]
    representative_poems: List[dict]
    alias: Optional[str] = None
    influence: Optional[int] = None
    styles: Optional[List[str]] = None
    description: Optional[str] = None
    relations: Optional[List[PoetRelationItem]] = None


@router.get("/data", response_model=GraphData)
async def get_graph_data(
    dynasty: Optional[str] = None,
    category: Optional[str] = None,
    min_poems: int = Query(5, ge=1, le=50),
    limit_per_dynasty: int = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"graph:data:{dynasty or '_'}:{category or '_'}:{min_poems}:{limit_per_dynasty}"
    cached = await cache_get(cache_key)
    if cached:
        return JSONResponse(content=cached)

    ANON_AUTHORS = {"无名氏", "佚名", "不详", "未知", "匿名", "阙名"}

    conds = []
    if dynasty:
        conds.append(Poem.dynasty == dynasty)
    if category:
        conds.append(Poem.category == category)

    def apply_conds(q):
        for c in conds:
            q = q.where(c)
        return q

    aq = apply_conds(
        select(Poem.author, Poem.dynasty, func.count(Poem.id).label("cnt"), func.min(Poem.title).label("rep"))
        .where(Poem.author.notin_(ANON_AUTHORS))
        .group_by(Poem.author, Poem.dynasty)
    ).having(func.count(Poem.id) >= min_poems)
    author_rows = (await db.execute(aq)).all()

    dynasty_limits = {"唐": 15, "宋": 15}
    default_limit = 8

    by_dynasty: dict = {}
    for r in author_rows:
        by_dynasty.setdefault(r[1], []).append(r)

    all_author_map = {r[0]: r for r in author_rows}

    selected_rows = []
    selected_names = set()
    for dyn, rows in by_dynasty.items():
        cap = limit_per_dynasty if limit_per_dynasty > 0 else dynasty_limits.get(dyn, default_limit)
        profile_rows = [r for r in rows if r[0] in POET_PROFILES]
        other_rows = sorted([r for r in rows if r[0] not in POET_PROFILES], key=lambda x: x[2], reverse=True)
        picked = profile_rows + other_rows[:max(0, cap - len(profile_rows))]
        selected_rows.extend(picked)
        for r in picked:
            selected_names.add(r[0])

    filtered_authors: dict = {}
    for r in selected_rows:
        filtered_authors[r[0]] = {"dynasty": r[1], "count": r[2], "representative": r[3], "categories": set()}

    categories = [
        {"name": "朝代"},
        {"name": "诗人"},
        {"name": "题材"},
    ]

    if not filtered_authors:
        empty_data = {"nodes": [], "links": [], "categories": categories}
        await cache_set(cache_key, empty_data, ttl=3600)
        return JSONResponse(content=empty_data)

    author_names = list(filtered_authors.keys())
    cat_expr = func.coalesce(Poem.category, "其他")
    acq = apply_conds(
        select(Poem.author, cat_expr.label("cat"), func.count(Poem.id).label("cnt"))
        .where(Poem.author.in_(author_names))
        .group_by(Poem.author, cat_expr)
    )
    dq = apply_conds(select(Poem.dynasty, func.count(Poem.id).label("cnt")).group_by(Poem.dynasty))

    async def run_cat_query():
        async with AsyncSessionLocal() as s:
            return (await s.execute(acq)).all()

    async def run_dynasty_query():
        async with AsyncSessionLocal() as s:
            return (await s.execute(dq)).all()

    ac_rows, dq_rows = await asyncio.gather(run_cat_query(), run_dynasty_query())

    author_cat_counts: dict = {}
    active_categories: dict = {}
    for r in ac_rows:
        if r[0] in filtered_authors:
            filtered_authors[r[0]]["categories"].add(r[1])
            author_cat_counts[(r[0], r[1])] = r[2]
            active_categories[r[1]] = active_categories.get(r[1], 0) + r[2]

    dynasty_data = {r[0]: r[1] for r in dq_rows}

    nodes: list[dict] = []
    links: list[dict] = []

    for dyn, count in dynasty_data.items():
        size = min(80, max(30, int(count ** 0.5 * 6)))
        nodes.append({
            "id": f"dynasty_{dyn}",
            "name": dyn,
            "category": 0,
            "value": count,
            "symbolSize": size,
            "poem_count": count,
        })

    for author, data in filtered_authors.items():
        profile = get_poet_profile(author)
        if profile:
            inf = profile["influence"]
            size = max(24, min(55, round(inf / 100 * 55)))
        else:
            size = min(50, max(12, int(data["count"] ** 0.5 * 5)))
        nodes.append({
            "id": f"author_{author}",
            "name": author,
            "category": 1,
            "value": data["count"],
            "symbolSize": size,
            "dynasty": data["dynasty"],
            "poem_count": data["count"],
            "representative_work": data["representative"],
            "alias": profile["alias"] if profile else None,
            "influence": profile["influence"] if profile else None,
            "styles": profile["styles"] if profile else None,
            "description": profile["description"] if profile else None,
        })

    for cat, count in active_categories.items():
        size = min(60, max(20, int(count ** 0.5 * 4)))
        nodes.append({
            "id": f"category_{cat}",
            "name": cat,
            "category": 2,
            "value": count,
            "symbolSize": size,
            "poem_count": count,
        })

    for author, data in filtered_authors.items():
        dyn = data["dynasty"]
        links.append({
            "source": f"author_{author}",
            "target": f"dynasty_{dyn}",
            "value": data["count"],
            "label": f"{dyn}代诗人",
        })

        sorted_cats = sorted(data["categories"], key=lambda c: author_cat_counts.get((author, c), 0), reverse=True)
        for cat in sorted_cats[:2]:
            cat_count = author_cat_counts.get((author, cat), 0)
            if cat_count > 0:
                links.append({
                    "source": f"author_{author}",
                    "target": f"category_{cat}",
                    "value": cat_count,
                    "label": f"擅长·{cat_count}首",
                })

    added_pairs = set()
    author_set = set(filtered_authors.keys())
    for rel in POET_RELATIONS:
        s, t = rel["source"], rel["target"]
        if s in author_set and t in author_set:
            pair_key = tuple(sorted([s, t]))
            if pair_key not in added_pairs:
                added_pairs.add(pair_key)
                links.append({
                    "source": f"author_{s}",
                    "target": f"author_{t}",
                    "value": 1,
                    "label": rel["label"],
                    "description": rel["description"],
                })

    same_dynasty_authors: dict = {}
    for author, data in filtered_authors.items():
        dyn = data["dynasty"]
        same_dynasty_authors.setdefault(dyn, []).append(author)

    for dyn, authors in same_dynasty_authors.items():
        if len(authors) <= 1:
            continue
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                pair_key = tuple(sorted([authors[i], authors[j]]))
                if pair_key in added_pairs:
                    continue
                shared = filtered_authors[authors[i]]["categories"] & filtered_authors[authors[j]]["categories"]
                if shared:
                    added_pairs.add(pair_key)
                    links.append({
                        "source": f"author_{authors[i]}",
                        "target": f"author_{authors[j]}",
                        "value": len(shared),
                        "label": "同代·同题",
                    })

    result_data = {"nodes": nodes, "links": links, "categories": categories}
    await cache_set(cache_key, result_data, ttl=3600)
    return JSONResponse(content=result_data)


class AIRelationRequest(BaseModel):
    poet_a: str
    poet_b: str


class AIRelationResponse(BaseModel):
    poet_a: str
    poet_b: str
    summary: str
    sections: List[dict]
    known_relation: Optional[str] = None


POET_RELATION_SYSTEM_PROMPT = """你是一位精通中国古典文学的学者。请简要介绍两位诗人的关系。

以JSON格式回复：
- summary: 一句话概括关系（不超过20字）
- sections: 2个section，每项含 title 和 content（各1-2句话）

语言典雅简练，严格输出合法JSON。"""


@router.post("/ai-relation", response_model=AIRelationResponse)
async def ai_poet_relation(
    req: AIRelationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if req.poet_a == req.poet_b:
        raise HTTPException(status_code=400, detail="请选择两位不同的诗人")

    cache_key = ":".join(sorted([req.poet_a, req.poet_b]))

    cached_row = await db.execute(
        select(PoetRelationCache).where(PoetRelationCache.cache_key == cache_key)
    )
    cached = cached_row.scalar_one_or_none()
    if cached:
        return JSONResponse(content={
            "poet_a": cached.poet_a,
            "poet_b": cached.poet_b,
            "summary": cached.summary,
            "sections": cached.sections,
            "known_relation": cached.known_relation,
        })

    profile_a = get_poet_profile(req.poet_a)
    profile_b = get_poet_profile(req.poet_b)

    q_a = select(Poem.author, Poem.dynasty, Poem.category, Poem.title).where(
        Poem.author == req.poet_a
    ).limit(10)
    q_b = select(Poem.author, Poem.dynasty, Poem.category, Poem.title).where(
        Poem.author == req.poet_b
    ).limit(10)
    r_a, r_b = (await db.execute(q_a)).all(), (await db.execute(q_b)).all()

    if not r_a and not profile_a:
        raise HTTPException(status_code=404, detail=f"未找到诗人「{req.poet_a}」")
    if not r_b and not profile_b:
        raise HTTPException(status_code=404, detail=f"未找到诗人「{req.poet_b}」")

    def build_info(name, profile, rows):
        dynasty = rows[0][1] if rows else ''
        titles = [r[3] for r in rows[:3]] if rows else []
        info = f"【{name}】{dynasty}，代表作{'、'.join(titles)}"
        if profile:
            desc = profile.get('description', '')[:50]
            info += f"，{desc}"
        return info

    info_a = build_info(req.poet_a, profile_a, r_a)
    info_b = build_info(req.poet_b, profile_b, r_b)

    known_label = get_relation_label(req.poet_a, req.poet_b)
    known_desc = ""
    if known_label:
        for r in POET_RELATIONS:
            if (r["source"] == req.poet_a and r["target"] == req.poet_b) or \
               (r["source"] == req.poet_b and r["target"] == req.poet_a):
                known_desc = f"已知关系：{r['label']} — {r['description']}"
                break

    prompt = f"{info_a}\n\n{info_b}"
    if known_desc:
        prompt += f"\n\n{known_desc}"
    prompt += f"\n\n请分析{req.poet_a}与{req.poet_b}的文学关系。"

    try:
        ai = get_ai_service()
        raw = await ai._call_llm(
            prompt=prompt,
            system_prompt=POET_RELATION_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=512,
            model_tier=AIModelTier.FLASH,
            response_format={"type": "json_object"},
            lite_guard=True,
        )
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="AI返回格式异常")
    except Exception as e:
        logger.error(f"AI关系解说失败: {e}")
        raise HTTPException(status_code=502, detail="AI服务暂时不可用")

    new_cache = PoetRelationCache(
        poet_a=req.poet_a,
        poet_b=req.poet_b,
        cache_key=cache_key,
        summary=data.get("summary", ""),
        sections=data.get("sections", []),
        known_relation=known_label,
    )
    db.add(new_cache)
    await db.commit()

    return JSONResponse(content={
        "poet_a": req.poet_a,
        "poet_b": req.poet_b,
        "summary": data.get("summary", ""),
        "sections": data.get("sections", []),
        "known_relation": known_label,
    })


@router.get("/dynasty-profiles")
async def get_dynasty_profiles():
    return DYNASTY_PROFILES


@router.get("/poet-profiles")
async def get_poet_profiles():
    return POET_PROFILES


@router.get("/poet-relations")
async def get_all_poet_relations():
    return POET_RELATIONS


@router.get("/dynasties")
async def get_dynasty_list(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("graph:dynasties")
    if cached:
        return cached
    query = select(Poem.dynasty, func.count(Poem.id).label("count")).group_by(Poem.dynasty).order_by(func.count(Poem.id).desc())
    result = await db.execute(query)
    rows = result.all()
    data = [{"name": row[0], "count": row[1]} for row in rows]
    await cache_set("graph:dynasties", data, ttl=3600)
    return data


@router.get("/categories")
async def get_category_list(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("graph:categories")
    if cached:
        return cached
    query = select(Poem.category, func.count(Poem.id).label("count")).where(Poem.category.isnot(None)).group_by(Poem.category).order_by(func.count(Poem.id).desc())
    result = await db.execute(query)
    rows = result.all()
    data = [{"name": row[0], "count": row[1]} for row in rows]
    await cache_set("graph:categories", data, ttl=300)
    return data


@router.get("/author/{author_name}", response_model=AuthorDetail)
async def get_author_detail(
    author_name: str,
    db: AsyncSession = Depends(get_db)
):
    meta_q = select(
        Poem.dynasty,
        func.count(Poem.id).label("poem_count"),
    ).where(Poem.author == author_name).group_by(Poem.dynasty)
    meta_result = await db.execute(meta_q)
    meta_row = meta_result.first()
    if not meta_row:
        raise HTTPException(status_code=404, detail="未找到该诗人")

    dynasty = meta_row.dynasty
    poem_count = meta_row.poem_count

    cat_q = select(Poem.category).where(
        Poem.author == author_name, Poem.category.isnot(None)
    ).group_by(Poem.category)
    cat_result = await db.execute(cat_q)
    categories = [r[0] or "其他" for r in cat_result.all()] or ["其他"]

    top_q = select(Poem.id, Poem.title, Poem.content).where(
        Poem.author == author_name
    ).order_by(func.coalesce(Poem.view_count, 0).desc()).limit(5)
    top_result = await db.execute(top_q)
    representative_poems = [
        {"id": r.id, "title": r.title, "content": r.content[:50]}
        for r in top_result.all()
    ]

    profile = get_poet_profile(author_name)
    rels = get_poet_relations(author_name)
    rel_items = [
        PoetRelationItem(
            target=r["target"] if r["source"] == author_name else r["source"],
            label=r["label"],
            description=r["description"]
        ) for r in rels
    ]

    return AuthorDetail(
        name=author_name,
        dynasty=dynasty,
        poem_count=poem_count,
        categories=categories,
        representative_poems=representative_poems,
        alias=profile["alias"] if profile else None,
        influence=profile["influence"] if profile else None,
        styles=profile["styles"] if profile else None,
        description=profile["description"] if profile else None,
        relations=rel_items if rel_items else None
    )

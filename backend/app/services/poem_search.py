from sqlalchemy import select, text, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.poem import Poem

TRGM_MIN_LENGTH = 3


async def search_poems_by_keyword(
    db: AsyncSession,
    keyword: str,
    limit: int = 30,
) -> list[Poem]:
    if len(keyword) >= TRGM_MIN_LENGTH:
        query = (
            select(Poem)
            .where(Poem.content.op("%%")(keyword))
            .order_by(func.similarity(Poem.content, keyword).desc())
            .limit(limit)
        )
        result = await db.execute(query)
        poems = result.scalars().all()
        if poems:
            return poems
    query = select(Poem).where(Poem.content.contains(keyword)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def search_poems_by_content(
    db: AsyncSession,
    content_fragment: str,
    limit: int = 5,
) -> list[Poem]:
    if len(content_fragment) >= TRGM_MIN_LENGTH:
        query = (
            select(Poem)
            .where(Poem.content.op("%%")(content_fragment))
            .order_by(func.similarity(Poem.content, content_fragment).desc())
            .limit(limit)
        )
        result = await db.execute(query)
        poems = result.scalars().all()
        if poems:
            return poems
    query = select(Poem).where(Poem.content.contains(content_fragment)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def match_poem_by_line(
    db: AsyncSession,
    line: str,
) -> Poem | None:
    clean_line = line.strip().rstrip("，。？！,")
    if not clean_line:
        return None
    if len(clean_line) >= TRGM_MIN_LENGTH:
        query = (
            select(Poem)
            .where(Poem.content.op("%%")(clean_line[:30]))
            .order_by(func.similarity(Poem.content, clean_line[:30]).desc())
            .limit(1)
        )
        result = await db.execute(query)
        poem = result.scalar_one_or_none()
        if poem:
            return poem
    query = select(Poem).where(Poem.content.contains(clean_line[:20])).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def search_poems_by_tags(
    db: AsyncSession,
    tags: list[str],
    limit: int = 5,
) -> list[Poem]:
    long_tags = [t for t in tags[:5] if len(t) >= TRGM_MIN_LENGTH]
    if long_tags:
        conditions = []
        for tag in long_tags:
            conditions.append(Poem.tags.op("%%")(tag))
            conditions.append(Poem.content.op("%%")(tag))
        query = select(Poem).where(or_(*conditions)).limit(limit)
        result = await db.execute(query)
        poems = result.scalars().all()
        if poems:
            return poems
    fallback_conditions = []
    for tag in tags[:5]:
        if Poem.tags is not None:
            fallback_conditions.append(Poem.tags.contains(tag))
        fallback_conditions.append(Poem.content.contains(tag))
    query = select(Poem).where(or_(*fallback_conditions)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


def extract_verses(poem: Poem, keyword: str) -> list[dict]:
    verses = []
    for line in poem.content.replace("\n", "，").split("，"):
        line = line.strip().rstrip("。？！")
        if keyword in line and line:
            verses.append({
                "content": line,
                "title": poem.title,
                "author": poem.author,
                "dynasty": poem.dynasty,
            })
    return verses

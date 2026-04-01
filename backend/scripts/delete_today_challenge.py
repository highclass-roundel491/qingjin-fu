import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def delete():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM challenge_submissions WHERE challenge_id IN (SELECT id FROM daily_challenges WHERE date = CURRENT_DATE)"))
        await conn.execute(text("DELETE FROM daily_challenges WHERE date = CURRENT_DATE"))
    print("已删除今日挑战及相关提交")
    await engine.dispose()

asyncio.run(delete())

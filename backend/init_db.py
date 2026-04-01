import asyncio
from app.core.database import engine, Base
from app.models.user import User
from app.models.poem import Poem
from app.models.learning import LearningRecord, PoemFavorite, UserStats
from app.models.challenge import DailyChallenge, ChallengeSubmission
from app.models.work import Work, WorkLike

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建成功")

if __name__ == "__main__":
    asyncio.run(init_db())

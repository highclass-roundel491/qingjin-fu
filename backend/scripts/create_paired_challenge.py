import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.challenge import DailyChallenge

async def create_challenge():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        today = date.today()
        
        challenge = DailyChallenge(
            date=today,
            sentence_template="寒江（）茶暖\n孤影（）故人",
            blank_count=2,
            theme="江边思友",
            mood="孤寂",
            hint="想象在寒江边，一个人的场景",
            difficulty="medium"
        )
        
        session.add(challenge)
        await session.commit()
        
        print(f"今日对仗挑战创建成功: {today}")
        print("寒江（）茶暖")
        print("孤影（）故人")

if __name__ == "__main__":
    asyncio.run(create_challenge())

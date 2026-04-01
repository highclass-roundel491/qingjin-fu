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
        
        challenges = [
            {
                "sentence_template": "寒江（）茶暖\n孤影（）故人",
                "blank_count": 2,
                "theme": "江边思友",
                "mood": "孤寂",
                "hint": "想象在寒江边，一个人的场景",
                "difficulty": "medium"
            },
            {
                "sentence_template": "春风（）柳绿\n细雨（）花红",
                "blank_count": 2,
                "theme": "春天",
                "mood": "生机",
                "hint": "春天的景象，风雨对花柳",
                "difficulty": "easy"
            },
            {
                "sentence_template": "明月（）思乡\n清风（）归梦",
                "blank_count": 2,
                "theme": "思乡",
                "mood": "惆怅",
                "hint": "月光和清风如何触动思乡之情",
                "difficulty": "medium"
            },
            {
                "sentence_template": "落花（）流水\n飞鸟（）白云",
                "blank_count": 2,
                "theme": "自然",
                "mood": "闲适",
                "hint": "花鸟与水云的关系",
                "difficulty": "easy"
            }
        ]
        
        import random
        selected = random.choice(challenges)
        
        challenge = DailyChallenge(
            date=today,
            sentence_template=selected["sentence_template"],
            blank_count=selected["blank_count"],
            theme=selected["theme"],
            mood=selected["mood"],
            hint=selected["hint"],
            difficulty=selected["difficulty"]
        )
        
        session.add(challenge)
        await session.commit()
        
        print(f"今日创意挑战创建成功: {today}")
        print(f"句子:\n{selected['sentence_template']}")
        print(f"主题: {selected['theme']}, 意境: {selected['mood']}")

if __name__ == "__main__":
    asyncio.run(create_challenge())

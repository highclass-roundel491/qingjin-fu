import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.challenge import DailyChallenge
from app.models.poem import Poem

async def create_challenge():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        today = date.today()
        
        query = select(Poem).where(Poem.dynasty == "唐").limit(100)
        result = await session.execute(query)
        poems = result.scalars().all()
        
        import random
        poem = random.choice(poems)
        
        lines = poem.content.strip().split('\n')
        if len(lines) >= 2:
            selected_lines = lines[:2]
        else:
            selected_lines = lines
        
        full_text = ''.join(selected_lines)
        
        if len(full_text) > 5:
            blank_pos = random.randint(2, len(full_text) - 3)
            original_char = full_text[blank_pos]
            
            challenge = DailyChallenge(
                date=today,
                poem_id=poem.id,
                original_content=''.join(selected_lines),
                blank_position=blank_pos,
                original_char=original_char,
                hint=f"出自{poem.author}《{poem.title}》",
                difficulty="medium"
            )
            
            session.add(challenge)
            await session.commit()
            
            print(f"今日挑战创建成功: {today}")
            print(f"诗句: {full_text}")
            print(f"空白位置: {blank_pos}, 原字: {original_char}")
        else:
            print("诗句太短，请重新运行")

if __name__ == "__main__":
    asyncio.run(create_challenge())

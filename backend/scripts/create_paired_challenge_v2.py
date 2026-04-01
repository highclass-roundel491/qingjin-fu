import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.challenge import DailyChallenge

async def create_paired_challenge():
    async with AsyncSessionLocal() as session:
        today = date.today()
        
        query = select(DailyChallenge).where(DailyChallenge.date == today)
        result = await session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"今日挑战已存在，正在更新...")
            existing.sentence_template = "春风吹__柳千条"
            existing.sentence_template_2 = "夏雨润__荷万朵"
            existing.blank_count = 1
            existing.theme = "四季"
            existing.mood = "清新"
            existing.hint = "填入一个动词，描绘春夏景象"
            existing.difficulty = "medium"
            await session.commit()
            print(f"更新成功！")
        else:
            challenge = DailyChallenge(
                date=today,
                sentence_template="春风吹__柳千条",
                sentence_template_2="夏雨润__荷万朵",
                blank_count=1,
                theme="四季",
                mood="清新",
                hint="填入一个动词，描绘春夏景象",
                difficulty="medium"
            )
            session.add(challenge)
            await session.commit()
            print(f"创建成功！")
        
        print(f"上句：春风吹__柳千条")
        print(f"下句：夏雨润__荷万朵")
        print(f"需填入：{1}个字")

if __name__ == "__main__":
    asyncio.run(create_paired_challenge())

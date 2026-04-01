import sys
import asyncio
sys.path.insert(0, '.')

from app.core.database import engine
from sqlalchemy import text

async def run():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, username, email FROM users LIMIT 10"))
        rows = result.fetchall()
        for row in rows:
            print(f"  id={row[0]}, username={row[1]}, email={row[2]}")
        if not rows:
            print("  No users found")

asyncio.run(run())

# backend/scripts/test_supabase.py
import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv(".env")


async def main():
    engine = create_async_engine(os.getenv("DATABASE_URL"))
    async with engine.connect() as conn:
        result = await conn.execute(
            __import__("sqlalchemy").text("SELECT COUNT(*) FROM vaults")
        )
        print("Connected! Vaults count:", result.scalar())
    await engine.dispose()


asyncio.run(main())

# backend/scripts/test_supabase.py
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def main():
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        result = await conn.execute(
            __import__("sqlalchemy").text("SELECT COUNT(*) FROM vaults")
        )
        print("Connected! Vaults count:", result.scalar())
    await engine.dispose()


asyncio.run(main())

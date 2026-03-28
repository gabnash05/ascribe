import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_database_is_reachable():
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_vaults_table_exists():
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM vaults"))
            count = result.scalar()
            assert count is not None  # table exists and is queryable
    finally:
        await engine.dispose()

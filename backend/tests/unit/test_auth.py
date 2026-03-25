# backend/tests/unit/test_auth.py
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_rejects_missing_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/test-auth")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rejects_invalid_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get(
            "/test-auth",
            headers={"Authorization": "Bearer invalid_token"},
        )

    assert resp.status_code == 401

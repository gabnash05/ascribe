"""
Shared fixtures for unit/routes/ and unit/services/.

Pytest walks up the directory tree, so everything defined here is
available to both subdirectories without any imports in the test files.

The root tests/conftest.py (worker fixtures) is untouched and continues
to work as before.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1 import ai, files, search, vaults
from app.core.clients import get_supabase
from app.core.database import get_db
from app.core.security import get_current_user

# ── stable IDs reused across all unit tests ───────────────────────────────────

USER_ID = uuid4()
VAULT_ID = uuid4()
FILE_ID = uuid4()


# ── database mock ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.execute = AsyncMock()
    return db


# ── supabase mock ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    client.storage.from_.return_value.upload = MagicMock()
    client.storage.from_.return_value.remove = MagicMock()
    return client


# ── ORM object factories ──────────────────────────────────────────────────────

# ── ORM object factories ──────────────────────────────────────────────────────
# Use SimpleNamespace instead of MagicMock so FastAPI's response_model
# serialization can read real attributes rather than auto-created Mock objects.


def make_vault(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        id=kwargs.get("id", VAULT_ID),
        user_id=kwargs.get("user_id", USER_ID),
        name=kwargs.get("name", "Test Vault"),
        description=kwargs.get("description", "A vault"),
        vault_metadata=kwargs.get("vault_metadata", {}),
        created_at=kwargs.get("created_at", "2024-01-01T00:00:00Z"),
        updated_at=kwargs.get("updated_at", "2024-01-01T00:00:00Z"),
    )


def make_file(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        id=kwargs.get("id", FILE_ID),
        vault_id=kwargs.get("vault_id", VAULT_ID),
        user_id=kwargs.get("user_id", USER_ID),
        original_name=kwargs.get("original_name", "test.pdf"),
        storage_path=kwargs.get("storage_path", f"{USER_ID}/{VAULT_ID}/test.pdf"),
        file_type=kwargs.get("file_type", "PDF"),
        mime_type=kwargs.get("mime_type", "application/pdf"),
        size_bytes=kwargs.get("size_bytes", 1024),
        page_count=kwargs.get("page_count", None),
        status=kwargs.get("status", "PROCESSING"),
        error_message=kwargs.get("error_message", None),
        total_chunks=kwargs.get("total_chunks", 0),
        total_tokens=kwargs.get("total_tokens", 0),
        file_metadata=kwargs.get("file_metadata", {}),
        created_at=kwargs.get("created_at", "2024-01-01T00:00:00Z"),
        updated_at=kwargs.get("updated_at", "2024-01-01T00:00:00Z"),
    )


# ── FastAPI app + HTTP client (used by routes/ tests only) ────────────────────


@pytest.fixture
def app(mock_db, mock_supabase):
    """FastAPI app with all external dependencies overridden."""
    application = FastAPI()
    application.include_router(vaults.router, prefix="/api/v1")
    application.include_router(files.router, prefix="/api/v1")
    application.include_router(search.router, prefix="/api/v1")
    application.include_router(ai.router, prefix="/api/v1")

    application.dependency_overrides[get_db] = lambda: mock_db
    application.dependency_overrides[get_supabase] = lambda: mock_supabase
    application.dependency_overrides[get_current_user] = lambda: USER_ID

    return application


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

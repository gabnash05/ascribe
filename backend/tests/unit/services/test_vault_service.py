from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.vault import VaultCreate, VaultUpdate
from app.services import vault_service

USER_ID = str(uuid4())
VAULT_ID = str(uuid4())


def _make_vault(name="My Vault", description="desc"):
    v = MagicMock()
    v.id = VAULT_ID
    v.user_id = USER_ID
    v.name = name
    v.description = description
    return v


def _scalar_result(obj):
    """Return a mock whose .scalar_one_or_none() returns obj."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = obj
    return result


def _scalars_result(items):
    """Return a mock whose .scalars().all() returns items."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


# ── create_vault ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_vault_adds_and_flushes():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    data = VaultCreate(name="My Vault", description="desc")

    with patch("app.services.vault_service.Vault") as MockVault:
        instance = _make_vault()
        MockVault.return_value = instance
        result = await vault_service.create_vault(db, USER_ID, data)

    db.add.assert_called_once_with(instance)
    db.flush.assert_awaited_once()
    db.refresh.assert_awaited_once_with(instance)
    assert result is instance


# ── list_vaults ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_vaults_returns_user_vaults():
    db = AsyncMock()
    vaults = [_make_vault("A"), _make_vault("B")]
    db.execute = AsyncMock(return_value=_scalars_result(vaults))

    result = await vault_service.list_vaults(db, USER_ID)

    assert result == vaults
    db.execute.assert_awaited_once()


# ── get_vault ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_vault_found():
    db = AsyncMock()
    vault = _make_vault()
    db.execute = AsyncMock(return_value=_scalar_result(vault))

    result = await vault_service.get_vault(db, VAULT_ID, USER_ID)

    assert result is vault


@pytest.mark.asyncio
async def test_get_vault_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))

    result = await vault_service.get_vault(db, VAULT_ID, USER_ID)

    assert result is None


# ── update_vault ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_vault_applies_partial_fields():
    db = AsyncMock()
    vault = _make_vault(name="Old Name")
    db.execute = AsyncMock(return_value=_scalar_result(vault))
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    data = VaultUpdate(name="New Name")
    result = await vault_service.update_vault(db, VAULT_ID, USER_ID, data)

    assert result.name == "New Name"
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_vault_not_found_returns_none():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))

    result = await vault_service.update_vault(
        db, VAULT_ID, USER_ID, VaultUpdate(name="X")
    )

    assert result is None


# ── delete_vault ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_vault_returns_true():
    db = AsyncMock()
    vault = _make_vault()
    db.execute = AsyncMock(return_value=_scalar_result(vault))
    db.delete = AsyncMock()
    db.flush = AsyncMock()

    result = await vault_service.delete_vault(db, VAULT_ID, USER_ID)

    assert result is True
    db.delete.assert_awaited_once_with(vault)


@pytest.mark.asyncio
async def test_delete_vault_not_found_returns_false():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))

    result = await vault_service.delete_vault(db, VAULT_ID, USER_ID)

    assert result is False

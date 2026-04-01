from unittest.mock import AsyncMock, patch

import pytest

from tests.unit.conftest import VAULT_ID, make_vault

BASE = "/api/v1/vaults"


@pytest.mark.asyncio
async def test_create_vault_201(client):
    vault = make_vault(name="New Vault")

    with patch(
        "app.api.v1.vaults.vault_service.create_vault", AsyncMock(return_value=vault)
    ):
        resp = await client.post(BASE, json={"name": "New Vault"})

    assert resp.status_code == 201
    assert resp.json()["name"] == "New Vault"


@pytest.mark.asyncio
async def test_list_vaults_200(client):
    vaults = [make_vault(name="A"), make_vault(name="B")]

    with patch(
        "app.api.v1.vaults.vault_service.list_vaults", AsyncMock(return_value=vaults)
    ):
        resp = await client.get(BASE)

    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_vault_200(client):
    vault = make_vault()

    with patch(
        "app.api.v1.vaults.vault_service.get_vault", AsyncMock(return_value=vault)
    ):
        resp = await client.get(f"{BASE}/{VAULT_ID}")

    assert resp.status_code == 200
    assert resp.json()["name"] == vault.name


@pytest.mark.asyncio
async def test_get_vault_404(client):
    with patch(
        "app.api.v1.vaults.vault_service.get_vault", AsyncMock(return_value=None)
    ):
        resp = await client.get(f"{BASE}/{VAULT_ID}")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_vault_200(client):
    vault = make_vault(name="Updated")

    with patch(
        "app.api.v1.vaults.vault_service.update_vault", AsyncMock(return_value=vault)
    ):
        resp = await client.put(f"{BASE}/{VAULT_ID}", json={"name": "Updated"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_vault_404(client):
    with patch(
        "app.api.v1.vaults.vault_service.update_vault", AsyncMock(return_value=None)
    ):
        resp = await client.put(f"{BASE}/{VAULT_ID}", json={"name": "X"})

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_vault_204(client):
    with patch(
        "app.api.v1.vaults.vault_service.delete_vault", AsyncMock(return_value=True)
    ):
        resp = await client.delete(f"{BASE}/{VAULT_ID}")

    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_vault_404(client):
    with patch(
        "app.api.v1.vaults.vault_service.delete_vault", AsyncMock(return_value=False)
    ):
        resp = await client.delete(f"{BASE}/{VAULT_ID}")

    assert resp.status_code == 404

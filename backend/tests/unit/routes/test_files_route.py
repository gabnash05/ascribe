from unittest.mock import AsyncMock, patch

import pytest

from tests.unit.conftest import FILE_ID, VAULT_ID, make_file

BASE = f"/api/v1/vaults/{VAULT_ID}/files"


@pytest.mark.asyncio
async def test_upload_file_202(client):
    record = make_file(status="PROCESSING")
    record.id = FILE_ID

    with patch(
        "app.api.v1.files.file_service.upload_file", AsyncMock(return_value=record)
    ):
        resp = await client.post(
            BASE,
            files={"file": ("test.pdf", b"PDF bytes", "application/pdf")},
        )

    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "PROCESSING"
    assert "file_id" in body


@pytest.mark.asyncio
async def test_upload_file_vault_not_found_404(client):
    with patch(
        "app.api.v1.files.file_service.upload_file",
        AsyncMock(side_effect=ValueError("Vault not found")),
    ):
        resp = await client.post(
            BASE,
            files={"file": ("test.pdf", b"bytes", "application/pdf")},
        )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_files_200(client):
    files = [make_file(), make_file()]

    with patch(
        "app.api.v1.files.file_service.list_files", AsyncMock(return_value=files)
    ):
        resp = await client.get(BASE)

    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_file_200(client):
    f = make_file(status="READY")

    with patch("app.api.v1.files.file_service.get_file", AsyncMock(return_value=f)):
        resp = await client.get(f"{BASE}/{FILE_ID}")

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_file_404(client):
    with patch("app.api.v1.files.file_service.get_file", AsyncMock(return_value=None)):
        resp = await client.get(f"{BASE}/{FILE_ID}")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_file_status_200(client):
    status_data = {"status": "ready", "error_message": None, "total_chunks": 42}

    with patch(
        "app.api.v1.files.file_service.get_file_status",
        AsyncMock(return_value=status_data),
    ):
        resp = await client.get(f"{BASE}/{FILE_ID}/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["total_chunks"] == 42
    assert body["file_id"] == str(FILE_ID)


@pytest.mark.asyncio
async def test_get_file_status_404(client):
    with patch(
        "app.api.v1.files.file_service.get_file_status", AsyncMock(return_value=None)
    ):
        resp = await client.get(f"{BASE}/{FILE_ID}/status")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_file_204(client):
    with patch(
        "app.api.v1.files.file_service.delete_file", AsyncMock(return_value=True)
    ):
        resp = await client.delete(f"{BASE}/{FILE_ID}")

    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_file_404(client):
    with patch(
        "app.api.v1.files.file_service.delete_file", AsyncMock(return_value=False)
    ):
        resp = await client.delete(f"{BASE}/{FILE_ID}")

    assert resp.status_code == 404

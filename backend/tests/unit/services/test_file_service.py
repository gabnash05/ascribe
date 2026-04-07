from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app.services import file_service

USER_ID = str(uuid4())
VAULT_ID = str(uuid4())
FILE_ID = str(uuid4())


def _make_vault():
    v = MagicMock()
    v.id = VAULT_ID
    v.user_id = USER_ID
    return v


def _make_file(status="PROCESSING"):
    f = MagicMock()
    f.id = FILE_ID
    f.vault_id = VAULT_ID
    f.user_id = USER_ID
    f.storage_path = f"{USER_ID}/{VAULT_ID}/test.pdf"
    f.status = status
    f.error_message = None
    f.total_chunks = 0
    return f


def _scalar_result(obj):
    r = MagicMock()
    r.scalar_one_or_none.return_value = obj
    return r


def _scalars_result(items):
    r = MagicMock()
    r.scalars.return_value.all.return_value = items
    return r


def _make_upload_file(filename="test.pdf", content=b"PDF content"):
    upload = MagicMock(spec=UploadFile)
    upload.filename = filename
    upload.content_type = "application/pdf"
    upload.size = len(content)
    upload.read = AsyncMock(return_value=content)
    return upload


# ── upload_file ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_file_happy_path():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    supabase = MagicMock()
    supabase.storage.from_.return_value.upload = MagicMock()

    upload = _make_upload_file()
    file_record = _make_file()

    with (
        patch(
            "app.services.file_service.vault_service.get_vault",
            AsyncMock(return_value=_make_vault()),
        ),
        patch("app.services.file_service.File", return_value=file_record),
        patch("app.services.file_service.ingest_file") as mock_task,
        patch("app.services.file_service.asyncio.to_thread", AsyncMock()),
    ):
        result = await file_service.upload_file(db, supabase, VAULT_ID, USER_ID, upload)

    db.add.assert_called_once()
    db.flush.assert_awaited_once()
    mock_task.delay.assert_called_once_with(str(file_record.id))
    assert result is file_record


@pytest.mark.asyncio
async def test_upload_file_vault_not_found_raises():
    db = AsyncMock()
    supabase = MagicMock()
    upload = _make_upload_file()

    with patch(
        "app.services.file_service.vault_service.get_vault",
        AsyncMock(return_value=None),
    ):
        with pytest.raises(ValueError, match="not found"):
            await file_service.upload_file(db, supabase, VAULT_ID, USER_ID, upload)


# ── list_files ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_files_returns_files():
    db = AsyncMock()
    files = [_make_file(), _make_file()]
    db.execute = AsyncMock(return_value=_scalars_result(files))

    with patch(
        "app.services.file_service.vault_service.get_vault",
        AsyncMock(return_value=_make_vault()),
    ):
        result = await file_service.list_files(db, VAULT_ID, USER_ID)

    assert result == files


@pytest.mark.asyncio
async def test_list_files_vault_not_found_raises():
    db = AsyncMock()

    with patch(
        "app.services.file_service.vault_service.get_vault",
        AsyncMock(return_value=None),
    ):
        with pytest.raises(ValueError):
            await file_service.list_files(db, VAULT_ID, USER_ID)


# ── get_file ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_file_found():
    db = AsyncMock()
    f = _make_file()
    db.execute = AsyncMock(return_value=_scalar_result(f))

    result = await file_service.get_file(db, FILE_ID, VAULT_ID, USER_ID)
    assert result is f


@pytest.mark.asyncio
async def test_get_file_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))

    result = await file_service.get_file(db, FILE_ID, VAULT_ID, USER_ID)
    assert result is None


# ── get_file_status ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_file_status_ready():
    db = AsyncMock()
    f = _make_file(status="READY")
    f.total_chunks = 12
    db.execute = AsyncMock(return_value=_scalar_result(f))

    result = await file_service.get_file_status(db, FILE_ID, VAULT_ID, USER_ID)

    assert result == {"status": "READY", "error_message": None, "total_chunks": 12}


@pytest.mark.asyncio
async def test_get_file_status_not_found_returns_none():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))

    result = await file_service.get_file_status(db, FILE_ID, VAULT_ID, USER_ID)
    assert result is None


# ── delete_file ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_file_happy_path():
    db = AsyncMock()
    f = _make_file()
    db.execute = AsyncMock(return_value=_scalar_result(f))
    db.delete = AsyncMock()
    db.flush = AsyncMock()
    supabase = MagicMock()

    with patch("app.services.file_service.asyncio.to_thread", AsyncMock()):
        result = await file_service.delete_file(
            db, supabase, FILE_ID, VAULT_ID, USER_ID
        )

    assert result is True
    db.delete.assert_awaited_once_with(f)


@pytest.mark.asyncio
async def test_delete_file_not_found_returns_false():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))
    supabase = MagicMock()

    result = await file_service.delete_file(db, supabase, FILE_ID, VAULT_ID, USER_ID)
    assert result is False


# ── vault_has_ready_files ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vault_has_ready_files_true():
    db = AsyncMock()
    r = MagicMock()
    r.scalar_one_or_none.return_value = FILE_ID
    db.execute = AsyncMock(return_value=r)

    with patch(
        "app.services.file_service.vault_service.get_vault",
        AsyncMock(return_value=_make_vault()),
    ):
        result = await file_service.vault_has_ready_files(db, VAULT_ID, USER_ID)

    assert result is True


@pytest.mark.asyncio
async def test_vault_has_ready_files_false_no_files():
    db = AsyncMock()
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=r)

    with patch(
        "app.services.file_service.vault_service.get_vault",
        AsyncMock(return_value=_make_vault()),
    ):
        result = await file_service.vault_has_ready_files(db, VAULT_ID, USER_ID)

    assert result is False


@pytest.mark.asyncio
async def test_vault_has_ready_files_false_vault_missing():
    db = AsyncMock()

    with patch(
        "app.services.file_service.vault_service.get_vault",
        AsyncMock(return_value=None),
    ):
        result = await file_service.vault_has_ready_files(db, VAULT_ID, USER_ID)

    assert result is False

"""
Unit tests for Pydantic schemas.
No database, no HTTP — pure validation logic only.
"""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.file import FileListResponse, FileResponse
from app.schemas.vault import VaultCreate, VaultListResponse, VaultResponse, VaultUpdate

# ── helpers ───────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _vault_response_data(**overrides) -> dict:
    return {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "name": "My Vault",
        "description": "A test vault",
        "metadata": {},
        "created_at": _now(),
        "updated_at": _now(),
        **overrides,
    }


def _file_response_data(**overrides) -> dict:
    return {
        "id": uuid.uuid4(),
        "vault_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "original_name": "lecture_notes.pdf",
        "file_type": "pdf",
        "mime_type": "application/pdf",
        "size_bytes": 204800,
        "page_count": 12,
        "status": "ready",
        "error_message": None,
        "total_chunks": 24,
        "total_tokens": 6800,
        "metadata": {},
        "created_at": _now(),
        "updated_at": _now(),
        **overrides,
    }


# ── VaultCreate ───────────────────────────────────────────────────────────────


class TestVaultCreate:
    def test_valid_minimal(self):
        v = VaultCreate(name="Biology 101")
        assert v.name == "Biology 101"
        assert v.description is None

    def test_valid_with_description(self):
        v = VaultCreate(name="Biology 101", description="Semester 1 notes")
        assert v.description == "Semester 1 notes"

    def test_name_empty_string_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            VaultCreate(name="")

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            VaultCreate(name="x" * 101)

    def test_name_exactly_100_chars_accepted(self):
        v = VaultCreate(name="x" * 100)
        assert len(v.name) == 100

    def test_description_too_long_rejected(self):
        with pytest.raises(ValidationError, match="description"):
            VaultCreate(name="Valid", description="x" * 501)

    def test_description_exactly_500_chars_accepted(self):
        v = VaultCreate(name="Valid", description="x" * 500)
        assert len(v.description) == 500

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            VaultCreate()


# ── VaultUpdate ───────────────────────────────────────────────────────────────


class TestVaultUpdate:
    def test_all_fields_optional(self):
        # A completely empty PATCH body should be valid
        v = VaultUpdate()
        assert v.name is None
        assert v.description is None

    def test_partial_name_only(self):
        v = VaultUpdate(name="Renamed Vault")
        assert v.name == "Renamed Vault"
        assert v.description is None

    def test_partial_description_only(self):
        v = VaultUpdate(description="Updated description")
        assert v.description == "Updated description"
        assert v.name is None

    def test_name_empty_string_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            VaultUpdate(name="")

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            VaultUpdate(name="x" * 101)

    def test_description_too_long_rejected(self):
        with pytest.raises(ValidationError, match="description"):
            VaultUpdate(description="x" * 501)


# ── VaultResponse ─────────────────────────────────────────────────────────────


class TestVaultResponse:
    def test_valid_full(self):
        data = _vault_response_data()
        v = VaultResponse(**data)
        assert v.name == "My Vault"
        assert isinstance(v.id, uuid.UUID)

    def test_description_nullable(self):
        data = _vault_response_data(description=None)
        v = VaultResponse(**data)
        assert v.description is None

    def test_metadata_defaults_to_empty_dict(self):
        data = _vault_response_data(metadata={})
        v = VaultResponse(**data)
        assert v.metadata == {}

    def test_metadata_with_content(self):
        data = _vault_response_data(metadata={"color": "blue", "pinned": True})
        v = VaultResponse(**data)
        assert v.metadata["color"] == "blue"

    def test_from_attributes(self):
        """Confirm model_config from_attributes works with a mock ORM object."""

        class FakeVault:
            id = uuid.uuid4()
            user_id = uuid.uuid4()
            name = "ORM Vault"
            description = None
            metadata = {}
            created_at = _now()
            updated_at = _now()

        v = VaultResponse.model_validate(FakeVault())
        assert v.name == "ORM Vault"

    def test_missing_required_field_rejected(self):
        data = _vault_response_data()
        del data["name"]
        with pytest.raises(ValidationError, match="name"):
            VaultResponse(**data)


# ── VaultListResponse ─────────────────────────────────────────────────────────


class TestVaultListResponse:
    def test_empty_list(self):
        r = VaultListResponse(vaults=[], total=0)
        assert r.vaults == []
        assert r.total == 0

    def test_with_vaults(self):
        vaults = [VaultResponse(**_vault_response_data()) for _ in range(3)]
        r = VaultListResponse(vaults=vaults, total=3)
        assert len(r.vaults) == 3
        assert r.total == 3

    def test_total_field_required(self):
        with pytest.raises(ValidationError, match="total"):
            VaultListResponse(vaults=[])


# ── FileResponse ──────────────────────────────────────────────────────────────


class TestFileResponse:
    def test_valid_full(self):
        f = FileResponse(**_file_response_data())
        assert f.original_name == "lecture_notes.pdf"
        assert f.status == "ready"

    def test_nullable_fields_accept_none(self):
        data = _file_response_data(
            mime_type=None,
            size_bytes=None,
            page_count=None,
            error_message=None,
        )
        f = FileResponse(**data)
        assert f.mime_type is None
        assert f.size_bytes is None
        assert f.page_count is None
        assert f.error_message is None

    def test_storage_path_not_present(self):
        """storage_path must not be a field on FileResponse."""
        f = FileResponse(**_file_response_data())
        assert not hasattr(f, "storage_path")

    def test_status_processing(self):
        f = FileResponse(**_file_response_data(status="processing"))
        assert f.status == "processing"

    def test_status_failed_with_error_message(self):
        f = FileResponse(
            **_file_response_data(
                status="failed",
                error_message="Docling could not parse this file.",
            )
        )
        assert f.status == "failed"
        assert f.error_message is not None

    def test_metadata_with_content(self):
        f = FileResponse(
            **_file_response_data(metadata={"ocr": True, "language": "en"})
        )
        assert f.metadata["ocr"] is True

    def test_from_attributes(self):
        class FakeFile:
            id = uuid.uuid4()
            vault_id = uuid.uuid4()
            user_id = uuid.uuid4()
            original_name = "notes.txt"
            file_type = "txt"
            mime_type = "text/plain"
            size_bytes = 1024
            page_count = None
            status = "ready"
            error_message = None
            total_chunks = 4
            total_tokens = 512
            metadata = {}
            created_at = _now()
            updated_at = _now()

        f = FileResponse.model_validate(FakeFile())
        assert f.original_name == "notes.txt"

    def test_missing_required_field_rejected(self):
        data = _file_response_data()
        del data["original_name"]
        with pytest.raises(ValidationError, match="original_name"):
            FileResponse(**data)


# ── FileListResponse ──────────────────────────────────────────────────────────


class TestFileListResponse:
    def test_empty_list(self):
        r = FileListResponse(files=[], total=0)
        assert r.files == []
        assert r.total == 0

    def test_with_files(self):
        files = [FileResponse(**_file_response_data()) for _ in range(2)]
        r = FileListResponse(files=files, total=2)
        assert len(r.files) == 2
        assert r.total == 2

    def test_total_field_required(self):
        with pytest.raises(ValidationError, match="total"):
            FileListResponse(files=[])

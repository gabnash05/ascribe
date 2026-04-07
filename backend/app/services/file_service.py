import asyncio
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client as SupabaseClient

from app.core.config import settings
from app.models.file import File
from app.services import vault_service
from app.workers.ingestion import ingest_file

MAX_FILE_SIZE = settings.max_file_size_bytes


async def upload_file(
    db: AsyncSession,
    supabase_client: SupabaseClient,
    vault_id: str,
    user_id: str,
    file: UploadFile,
) -> File:
    vault = await vault_service.get_vault(db, vault_id, user_id)
    if vault is None:
        raise ValueError(f"Vault {vault_id} not found or access denied.")

    original_name = file.filename or "upload"
    storage_path = f"{user_id}/{vault_id}/{uuid4()}_{original_name}"

    if file.size and file.size > MAX_FILE_SIZE:
        raise ValueError(
            f"File size exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )

    content = await file.read()
    size_bytes = len(content)

    if size_bytes > MAX_FILE_SIZE:
        raise ValueError(
            f"File size exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )
    await asyncio.to_thread(
        supabase_client.storage.from_(settings.supabase_storage_bucket).upload,
        storage_path,
        content,
    )

    record = File(
        vault_id=vault_id,
        user_id=user_id,
        storage_path=storage_path,
        original_name=original_name,
        file_type=_infer_file_type(original_name),
        mime_type=file.content_type,
        size_bytes=size_bytes,
        status="PROCESSING",
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    ingest_file.delay(str(record.id))

    return record


async def list_files(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
) -> list[File]:
    vault = await vault_service.get_vault(db, vault_id, user_id)
    if vault is None:
        raise ValueError(f"Vault {vault_id} not found or access denied.")

    result = await db.execute(
        select(File).where(File.vault_id == vault_id).order_by(File.created_at.desc())
    )
    return list(result.scalars().all())


async def get_file(
    db: AsyncSession,
    file_id: str,
    vault_id: str,
    user_id: str,
) -> File | None:
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.vault_id == vault_id,
            File.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_file_status(
    db: AsyncSession,
    file_id: str,
    vault_id: str,
    user_id: str,
) -> dict | None:
    file = await get_file(db, file_id, vault_id, user_id)
    if file is None:
        return None
    return {
        "status": file.status,
        "error_message": file.error_message,
        "total_chunks": file.total_chunks,
    }


async def delete_file(
    db: AsyncSession,
    supabase_client: SupabaseClient,
    file_id: str,
    vault_id: str,
    user_id: str,
) -> bool:
    file = await get_file(db, file_id, vault_id, user_id)
    if file is None:
        return False

    storage_path = file.storage_path

    await asyncio.to_thread(
        supabase_client.storage.from_(settings.supabase_storage_bucket).remove,
        [storage_path],
    )

    await db.delete(file)
    await db.flush()
    return True


# ── helpers ──────────────────────────────────────────────────────────────────

_EXT_MAP = {
    # PDF
    ".pdf": "PDF",
    # DOCX
    ".docx": "DOCX",
    ".doc": "DOCX",  # Legacy .doc files map to DOCX (handled by python-docx)
    # TXT
    ".txt": "TXT",
    ".text": "TXT",
    ".md": "TXT",
    ".markdown": "TXT",
    ".mdown": "TXT",
    ".mkd": "TXT",
    ".mkdn": "TXT",
    # IMAGE
    ".png": "IMAGE",
    ".jpg": "IMAGE",
    ".jpeg": "IMAGE",
    ".gif": "IMAGE",
    ".webp": "IMAGE",
    ".bmp": "IMAGE",
    ".svg": "IMAGE",
    ".ico": "IMAGE",
    ".tiff": "IMAGE",
    ".tif": "IMAGE",
    # Additional document formats (optional - map to appropriate types)
    ".rtf": "DOCX",  # Rich Text Format - can be processed as document
    ".odt": "DOCX",  # OpenDocument Text - LibreOffice format
    ".html": "NOTE",  # HTML can be treated as markdown-like
    ".htm": "NOTE",  # Same as above
    ".xml": "TXT",  # XML as plain text
    ".json": "TXT",  # JSON as plain text
    ".csv": "TXT",  # CSV as plain text
    ".log": "TXT",  # Log files as plain text
}


def _infer_file_type(filename: str) -> str:
    import os

    ext = os.path.splitext(filename)[1].lower()
    return _EXT_MAP.get(ext, "txt")


async def vault_has_ready_files(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
) -> bool:
    """
    Return True if the vault contains at least one file with status='ready'.
    Used as a guard before AI feature calls.
    Ownership is enforced by checking user_id via vault_service.
    """
    vault = await vault_service.get_vault(db, vault_id, user_id)
    if vault is None:
        return False

    result = await db.execute(
        select(File.id)
        .where(File.vault_id == vault_id, File.status == "READY")
        .limit(1)
    )
    return result.scalar_one_or_none() is not None

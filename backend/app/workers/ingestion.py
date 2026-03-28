from __future__ import annotations

import logging
import os
import tempfile
from typing import Any

from celery import Task
from sqlalchemy import create_engine, delete, insert, select, update
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.enums import FileStatusEnum
from app.models.chunk import Chunk
from app.models.file import File
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# ── Tuneable limits ────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB — reject before extraction
MAX_EXTRACTED_CHARS: int = 500_000  # ~350 pages of dense text
MAX_CHUNKS: int = 2_000  # safety ceiling after chunking
CHUNK_INSERT_BATCH: int = 500  # rows per DB transaction
EMBED_BATCH_SIZE: int = 64  # sentences per encoding call


# ── Exception hierarchy ────────────────────────────────────────────────────


class NonRetryableError(Exception):
    """Raised for failures where retrying will never succeed."""


# ── Singletons ─────────────────────────────────────────────────────────────

_sync_engine = None
_SyncSession: sessionmaker | None = None


def _get_session() -> Session:
    global _sync_engine, _SyncSession
    if _sync_engine is None:
        url = make_url(settings.database_url)
        sync_driver = url.drivername.replace("+asyncpg", "").replace("+aiopg", "")
        sync_url = str(url.set(drivername=sync_driver))
        _sync_engine = create_engine(sync_url, pool_pre_ping=True)
        _SyncSession = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSession()


_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading bge-small-en-v1.5 — one-time warm-up...")
        _embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        logger.info("Embedding model ready.")
    return _embedding_model


_supabase_client = None


def _get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client

        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _supabase_client


# ── Pipeline helpers ───────────────────────────────────────────────────────


def _download_file(storage_path: str, dest_path: str) -> int:
    """
    Download file from Supabase Storage into dest_path.
    Returns the file size in bytes so the caller can enforce the size limit
    before handing the file to Docling.
    """
    client = _get_supabase_client()
    data: bytes = client.storage.from_(settings.supabase_storage_bucket).download(
        storage_path
    )
    with open(dest_path, "wb") as fh:
        fh.write(data)
    return len(data)


def _extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[-1].lower()

    if ext in (".txt", ".md", ".markdown"):
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            return fh.read()

    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown(traverse_pictures=True)


def _clean_text(text: str) -> str:
    import re

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    return text.strip()


def _chunk_text(text: str) -> list[str]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    # chunk_size=450:
    #     Lower than 512 to avoid truncation, but higher than ~350 so chunks still hold full ideas.
    #     450 is the middle point: 512 risks cutoff, ~300–350 fragments context too much.

    # chunk_overlap=50 (~11%):
    #     Lower than ~80–100 to avoid heavy duplication, but higher than ~20–30 so boundaries are covered.
    #     50 keeps continuity without inflating storage or noise.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [c for c in splitter.split_text(text) if c.strip()]


def _embed(texts: list[str]) -> list[list[float]]:
    """
    Encode in batches of EMBED_BATCH_SIZE to avoid OOM on very long documents.
    Returns one flat list of vectors in the same order as texts.
    """
    model = _get_embedding_model()
    all_vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        vecs = model.encode(
            batch,
            batch_size=EMBED_BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        all_vectors.extend(vecs.tolist())
    return all_vectors


def _bulk_insert_chunks(
    db: Session,
    file_id: str,
    vault_id: str,
    chunks: list[str],
    vectors: list[list[float]],
) -> None:
    """
    Insert chunk rows in batches of CHUNK_INSERT_BATCH, committing after
    each batch. This prevents a single long-running transaction when a
    document produces hundreds or thousands of chunks.
    """
    rows = [
        {
            "file_id": file_id,
            "vault_id": vault_id,
            "content": text,
            "embedding": vector,
            "chunk_index": idx,
        }
        for idx, (text, vector) in enumerate(zip(chunks, vectors, strict=False))
    ]

    for batch_start in range(0, len(rows), CHUNK_INSERT_BATCH):
        batch = rows[batch_start : batch_start + CHUNK_INSERT_BATCH]
        db.execute(insert(Chunk), batch)
        db.commit()
        logger.info(
            "[%s] Inserted chunks %d–%d",
            file_id,
            batch_start,
            batch_start + len(batch) - 1,
        )


def _mark_failed(db: Session, file_id: str) -> None:
    """Roll back any open transaction and mark the file as FAILED."""
    db.rollback()
    try:
        db.execute(
            update(File).where(File.id == file_id).values(status=FileStatusEnum.FAILED)
        )
        db.commit()
    except Exception:
        logger.exception("[%s] Could not set FAILED status", file_id)


def _download_and_extract(file_row: File, file_id: str) -> str:
    """Download the file to a temp path, extract text, then delete the temp file."""
    suffix = os.path.splitext(file_row.original_name or "")[-1] or ".bin"
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(tmp_fd)

    try:
        file_size = _download_file(file_row.storage_path, tmp_path)
        logger.info("[%s] Downloaded %d bytes", file_id, file_size)

        if file_size > MAX_FILE_SIZE_BYTES:
            raise NonRetryableError(
                f"File {file_id} is {file_size} bytes — exceeds "
                f"{MAX_FILE_SIZE_BYTES} byte limit."
            )

        raw_text = _extract_text(tmp_path)
        logger.info("[%s] Extracted %d characters", file_id, len(raw_text))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return raw_text


def _validate_and_chunk(raw_text: str, file_id: str) -> list[str]:
    """Validate extracted text and split it into chunks."""
    if not raw_text.strip():
        raise NonRetryableError(f"Docling extracted no text from file {file_id}.")

    if len(raw_text) > MAX_EXTRACTED_CHARS:
        raise NonRetryableError(
            f"File {file_id} produced {len(raw_text)} characters — exceeds "
            f"{MAX_EXTRACTED_CHARS} character limit. Split the document and re-upload."
        )

    chunks = _chunk_text(_clean_text(raw_text))

    if not chunks:
        raise NonRetryableError(f"No usable chunks produced for file {file_id}.")

    if len(chunks) > MAX_CHUNKS:
        raise NonRetryableError(
            f"File {file_id} produced {len(chunks)} chunks — exceeds "
            f"{MAX_CHUNKS} chunk limit."
        )

    return chunks


def _run_pipeline(db: Session, file_id: str) -> dict[str, Any]:
    """
    Execute the full ingestion pipeline for a single file.
    All non-retryable failures raise NonRetryableError; everything else
    propagates as-is so the Celery task can schedule a retry.
    """
    # ── 1. Fetch file record ───────────────────────────────────────────────
    file_row: File | None = db.execute(
        select(File).where(File.id == file_id)
    ).scalar_one_or_none()

    if file_row is None:
        raise NonRetryableError(f"File {file_id} not found in database.")

    # ── 2. Idempotency: skip if already complete ───────────────────────────
    if file_row.status == FileStatusEnum.READY:
        logger.info("[%s] Already READY — skipping.", file_id)
        return {"file_id": file_id, "status": "skipped"}

    # ── 3. Clean slate: delete any chunks from a previous attempt ─────────
    deleted = db.execute(delete(Chunk).where(Chunk.file_id == file_id)).rowcount
    if deleted:
        logger.info("[%s] Deleted %d stale chunk(s) from prior run.", file_id, deleted)

    db.execute(
        update(File).where(File.id == file_id).values(status=FileStatusEnum.PROCESSING)
    )
    db.commit()
    logger.info("[%s] Status → PROCESSING", file_id)

    # ── 4. Download + extract ──────────────────────────────────────────────
    raw_text = _download_and_extract(file_row, file_id)

    # ── 5. Validate + chunk ────────────────────────────────────────────────
    chunks = _validate_and_chunk(raw_text, file_id)
    logger.info("[%s] %d chunks ready for embedding", file_id, len(chunks))

    # ── 6. Embed ───────────────────────────────────────────────────────────
    vectors = _embed(chunks)
    logger.info("[%s] Embeddings generated", file_id)

    # ── 7. Bulk insert (batched commits) ───────────────────────────────────
    _bulk_insert_chunks(db, file_id, str(file_row.vault_id), chunks, vectors)

    # ── 8. Mark ready ──────────────────────────────────────────────────────
    db.execute(
        update(File)
        .where(File.id == file_id)
        .values(status=FileStatusEnum.READY, total_chunks=len(chunks))
    )
    db.commit()

    logger.info("[%s] Status → READY (%d chunks)", file_id, len(chunks))
    return {"file_id": file_id, "chunks": len(chunks), "status": "ready"}


# ── Celery task ────────────────────────────────────────────────────────────


@celery_app.task(
    bind=True,
    max_retries=3,
)
def ingest_file(self: Task, file_id: str) -> dict[str, Any]:
    """
    Full ingestion pipeline for a single file.

    Idempotency contract
    ────────────────────
    - If the file is already READY, the task exits immediately (safe to
      re-enqueue without side effects).
    - At the start of every non-READY run, all existing Chunk rows for
      this file are deleted. Every retry therefore starts from a clean
      slate — no duplicate chunks can accumulate.

    Non-retryable errors (NonRetryableError)
    ─────────────────────────────────────────
    - File row not found in DB.
    - Downloaded file exceeds MAX_FILE_SIZE_BYTES.
    - Docling extracted no text.
    - Text exceeds MAX_EXTRACTED_CHARS.
    - Chunking produced no usable chunks.
    These are deterministic failures. Retrying wastes resources and retry
    budget, so the task marks the file FAILED and stops immediately.

    Retryable errors
    ─────────────────
    - Everything else (network blip, transient DB error, Docling crash).
    - Retried up to max_retries times with exponential backoff (30s, 60s, 120s).
    """
    db: Session = _get_session()
    try:
        return _run_pipeline(db, file_id)
    except NonRetryableError as exc:
        _mark_failed(db, file_id)
        logger.error("[%s] Non-retryable failure: %s", file_id, exc)
        raise
    except Exception as exc:
        _mark_failed(db, file_id)
        countdown = 30 * (2**self.request.retries)
        logger.warning(
            "[%s] Retryable failure (attempt %d/%d, retry in %ds): %s",
            file_id,
            self.request.retries + 1,
            self.max_retries,
            countdown,
            exc,
        )
        raise self.retry(exc=exc, countdown=countdown) from exc
    finally:
        db.close()

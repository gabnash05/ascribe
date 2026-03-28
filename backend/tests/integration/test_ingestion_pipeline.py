import os

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import FileStatusEnum
from app.models.chunk import Chunk
from app.models.file import File
from app.workers.ingestion import NonRetryableError

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _patch_session_factory(db: Session):
    """
    Redirect the worker's _get_session() to use the test transaction session
    so integration tests share the same rollback boundary.
    """
    from unittest.mock import patch

    with patch("app.workers.ingestion._get_session", return_value=db):
        yield


@pytest.fixture(autouse=True)
def _patch_download(test_file):
    """
    Replace Supabase Storage download with a local file copy.
    The worker still opens the file, extracts, and chunks it — only
    the network call is bypassed.
    """
    import shutil
    from unittest.mock import patch

    _, local_path = test_file

    def fake_download(storage_path: str, dest_path: str):
        shutil.copy(local_path, dest_path)
        return os.path.getsize(local_path)

    with patch("app.workers.ingestion._download_file", side_effect=fake_download):
        yield


class TestFullIngestionPipeline:
    def test_status_transitions_to_ready(self, db: Session, test_file):
        from app.workers.ingestion import ingest_file

        file_row, _ = test_file
        file_id = file_row.id

        ingest_file(file_row.id)

        refreshed = db.get(File, file_id)
        assert refreshed.status == FileStatusEnum.READY

    def test_chunks_are_inserted_into_db(self, db: Session, test_file):
        from app.workers.ingestion import ingest_file

        file_row, _ = test_file

        ingest_file(file_row.id)

        chunks = (
            db.execute(select(Chunk).where(Chunk.file_id == file_row.id))
            .scalars()
            .all()
        )

        assert len(chunks) > 0

    def test_chunk_count_matches_file_total_chunks(self, db: Session, test_file):
        from app.workers.ingestion import ingest_file

        file_row, _ = test_file
        file_id = file_row.id

        ingest_file(file_row.id)

        chunks = (
            db.execute(select(Chunk).where(Chunk.file_id == file_row.id))
            .scalars()
            .all()
        )

        refreshed = db.get(File, file_id)
        assert refreshed.total_chunks == len(chunks)

    def test_every_chunk_has_an_embedding(self, db: Session, test_file):
        from app.workers.ingestion import ingest_file

        file_row, _ = test_file

        ingest_file(file_row.id)

        chunks = (
            db.execute(select(Chunk).where(Chunk.file_id == file_row.id))
            .scalars()
            .all()
        )

        for chunk in chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 384

    def test_every_chunk_has_non_empty_content(self, db: Session, test_file):
        from app.workers.ingestion import ingest_file

        file_row, _ = test_file

        ingest_file(file_row.id)

        chunks = (
            db.execute(select(Chunk).where(Chunk.file_id == file_row.id))
            .scalars()
            .all()
        )

        for chunk in chunks:
            assert chunk.content.strip() != ""

    def test_chunks_are_scoped_to_correct_vault(
        self, db: Session, test_file, test_vault
    ):
        from app.workers.ingestion import ingest_file

        file_row, _ = test_file

        ingest_file(file_row.id)

        chunks = (
            db.execute(select(Chunk).where(Chunk.file_id == file_row.id))
            .scalars()
            .all()
        )

        for chunk in chunks:
            assert str(chunk.vault_id) == str(test_vault.id)

    def test_chunk_indexes_are_sequential_from_zero(self, db: Session, test_file):
        from app.workers.ingestion import ingest_file

        file_row, _ = test_file

        ingest_file(file_row.id)

        chunks = (
            db.execute(
                select(Chunk)
                .where(Chunk.file_id == file_row.id)
                .order_by(Chunk.chunk_index)
            )
            .scalars()
            .all()
        )

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i


class TestIngestionFailurePaths:
    def test_status_set_to_failed_when_file_row_missing(self, db: Session):
        from app.workers.ingestion import ingest_file

        bogus_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(NonRetryableError):
            ingest_file(bogus_id)

    def test_status_set_to_failed_when_extraction_returns_empty(
        self, db: Session, test_file
    ):
        from unittest.mock import patch

        from app.workers.ingestion import ingest_file

        file_row, _ = test_file
        file_id = file_row.id

        with patch("app.workers.ingestion._extract_text", return_value=""):
            with pytest.raises(NonRetryableError):
                ingest_file(file_id)

        refreshed = db.get(File, file_id)
        assert refreshed.status == FileStatusEnum.FAILED

    def test_no_chunks_inserted_on_failure(self, db: Session, test_file):
        from unittest.mock import patch

        from app.workers.ingestion import ingest_file

        file_row, _ = test_file

        with patch("app.workers.ingestion._extract_text", return_value=""):
            with pytest.raises(NonRetryableError):
                ingest_file(file_row.id)

        chunks = (
            db.execute(select(Chunk).where(Chunk.file_id == file_row.id))
            .scalars()
            .all()
        )

        assert len(chunks) == 0

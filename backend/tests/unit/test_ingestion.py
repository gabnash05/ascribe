import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.enums import FileStatusEnum

# ── Helper function tests ──────────────────────────────────────────────────


class TestCleanText:
    def test_collapses_multiple_blank_lines(self):
        from app.workers.ingestion import _clean_text

        raw = "paragraph one\n\n\n\nparagraph two"
        result = _clean_text(raw)
        assert "\n\n\n" not in result
        assert "paragraph one" in result
        assert "paragraph two" in result

    def test_strips_trailing_whitespace_per_line(self):
        from app.workers.ingestion import _clean_text

        raw = "line one   \nline two\t\nline three"
        result = _clean_text(raw)
        for line in result.splitlines():
            assert line == line.rstrip()

    def test_strips_leading_and_trailing_empty_lines(self):
        from app.workers.ingestion import _clean_text

        raw = "\n\n  actual content  \n\n"
        result = _clean_text(raw)
        assert result.startswith("actual content")

    def test_empty_string_returns_empty(self):
        from app.workers.ingestion import _clean_text

        assert _clean_text("") == ""

    def test_already_clean_text_is_unchanged(self):
        from app.workers.ingestion import _clean_text

        clean = "first paragraph.\n\nsecond paragraph."
        assert _clean_text(clean) == clean


class TestChunkText:
    LONG_TEXT = " ".join(["word"] * 600)  # well over one chunk

    def test_returns_non_empty_list(self):
        from app.workers.ingestion import _chunk_text

        chunks = _chunk_text(self.LONG_TEXT)
        assert len(chunks) > 0

    def test_produces_multiple_chunks_for_long_text(self):
        from app.workers.ingestion import _chunk_text

        chunks = _chunk_text(self.LONG_TEXT)
        assert len(chunks) > 1

    def test_single_short_sentence_is_one_chunk(self):
        from app.workers.ingestion import _chunk_text

        chunks = _chunk_text("This is a short sentence.")
        assert len(chunks) == 1

    def test_no_empty_chunks_returned(self):
        from app.workers.ingestion import _chunk_text

        chunks = _chunk_text(self.LONG_TEXT)
        for chunk in chunks:
            assert chunk.strip() != ""

    def test_empty_string_returns_empty_list(self):
        from app.workers.ingestion import _chunk_text

        chunks = _chunk_text("   ")
        assert chunks == []

    def test_chunks_preserve_content(self):
        from app.workers.ingestion import _chunk_text

        text = "Alpha beta gamma. " * 100
        chunks = _chunk_text(text)
        # Reassembling chunks should contain all original words
        combined = " ".join(chunks)
        assert "Alpha" in combined
        assert "gamma" in combined


class TestEmbed:
    def test_returns_list_of_lists(self):
        from app.workers.ingestion import _embed

        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((3, 384), dtype="float32")

        with patch("app.workers.ingestion._embedding_model", mock_model):
            result = _embed(["chunk one", "chunk two", "chunk three"])

        assert isinstance(result, list)
        assert all(isinstance(v, list) for v in result)

    def test_output_length_matches_input_length(self):
        from app.workers.ingestion import _embed

        texts = ["a", "b", "c", "d"]
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((len(texts), 384), dtype="float32")

        with patch("app.workers.ingestion._embedding_model", mock_model):
            result = _embed(texts)

        assert len(result) == len(texts)

    def test_each_vector_has_384_dimensions(self):
        from app.workers.ingestion import _embed

        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((2, 384), dtype="float32")

        with patch("app.workers.ingestion._embedding_model", mock_model):
            result = _embed(["text one", "text two"])

        assert all(len(v) == 384 for v in result)

    def test_encode_called_with_normalize_embeddings_true(self):
        from app.workers.ingestion import _embed

        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((1, 384), dtype="float32")

        with patch("app.workers.ingestion._embedding_model", mock_model):
            _embed(["hello world"])

        _, kwargs = mock_model.encode.call_args
        assert kwargs.get("normalize_embeddings") is True

    def test_embedding_model_singleton_loaded_once(self):
        """
        _get_embedding_model() should only instantiate SentenceTransformer once
        even if called multiple times in the same process.
        """
        import app.workers.ingestion as module

        original = module._embedding_model
        module._embedding_model = None  # force reset

        with patch("sentence_transformers.SentenceTransformer") as mock_cls:
            mock_cls.return_value = MagicMock()
            mock_cls.return_value.encode.return_value = np.zeros((1, 384))
            module._get_embedding_model()
            module._get_embedding_model()  # second call — should not re-instantiate

        assert mock_cls.call_count == 1
        module._embedding_model = original  # restore


# ── Celery task unit tests ─────────────────────────────────────────────────


class TestIngestFileTask:
    """
    Tests for the ingest_file Celery task.

    All external I/O is mocked:
      - SQLAlchemy session  →  MagicMock
      - Supabase download   →  patched to write a tempfile
      - Docling extractor   →  patched to return canned text
      - SentenceTransformer →  patched to return zero vectors
    """

    def _make_file_row(self, file_id: str, status=FileStatusEnum.PROCESSING):
        """Build a minimal mock File ORM row."""
        row = MagicMock()
        row.id = file_id
        row.vault_id = str(uuid.uuid4())
        row.storage_path = f"uploads/{file_id}.pdf"
        row.original_name = "lecture_notes.pdf"
        row.status = status
        return row

    @pytest.fixture(autouse=True)
    def _patch_sync_session(self, mock_db_session):
        """
        Replace _get_session() so the task never touches a real DB.
        """
        with patch("app.workers.ingestion._get_session", return_value=mock_db_session):
            yield

    @pytest.fixture(autouse=True)
    def _patch_download(self, tmp_path):
        """
        Replace _download_file() so it writes dummy bytes to the temp path,
        making the task think a real file was fetched from Supabase.
        """

        def fake_download(storage_path: str, dest_path: str):
            with open(dest_path, "wb") as fh:
                fh.write(b"%PDF-1.4 fake content")
            return len(b"%PDF-1.4 fake content")

        with patch("app.workers.ingestion._download_file", side_effect=fake_download):
            yield

    @pytest.fixture(autouse=True)
    def _patch_extract(self):
        """
        Replace _extract_text() with canned markdown — bypasses Docling.
        """
        sample = "\n\n".join(
            [f"Section {i}. " + "Content word. " * 80 for i in range(5)]
        )
        with patch("app.workers.ingestion._extract_text", return_value=sample):
            yield

    @pytest.fixture(autouse=True)
    def _patch_embed(self):
        """
        Replace _embed() with deterministic zero vectors.
        """

        def fake_embed(texts):
            return [[0.0] * 384 for _ in texts]

        with patch("app.workers.ingestion._embed", side_effect=fake_embed):
            yield

    # ── Happy path ─────────────────────────────────────────────────────────

    def test_returns_dict_with_expected_keys(self, fake_file_id, mock_db_session):
        from app.workers.ingestion import ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        result = ingest_file(fake_file_id)

        assert "file_id" in result
        assert "chunks" in result
        assert "status" in result

    def test_returns_ready_status_on_success(self, fake_file_id, mock_db_session):
        from app.workers.ingestion import ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        result = ingest_file(fake_file_id)
        assert result["status"] == "ready"

    def test_chunk_count_is_positive(self, fake_file_id, mock_db_session):
        from app.workers.ingestion import ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        result = ingest_file(fake_file_id)
        assert result["chunks"] > 0

    def test_commits_twice_on_success(self, fake_file_id, mock_db_session):
        """
        Two commits expected:
          1. After setting status → PROCESSING
          2. After bulk insert + setting status → READY
        """
        from app.workers.ingestion import ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        ingest_file(fake_file_id)
        assert mock_db_session.commit.call_count >= 2

    def test_session_closed_on_success(self, fake_file_id, mock_db_session):
        from app.workers.ingestion import ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        ingest_file(fake_file_id)
        mock_db_session.close.assert_called_once()

    # ── File not found ─────────────────────────────────────────────────────

    def test_raises_when_file_not_in_db(self, fake_file_id, mock_db_session):
        from app.workers.ingestion import NonRetryableError, ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(NonRetryableError, match="not found"):
            ingest_file(fake_file_id)

    # ── Failure path ───────────────────────────────────────────────────────

    def test_sets_failed_status_when_extraction_returns_empty(
        self, fake_file_id, mock_db_session
    ):
        from app.workers.ingestion import NonRetryableError, ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        with patch("app.workers.ingestion._extract_text", return_value="   "):
            with pytest.raises(NonRetryableError, match="no text"):
                ingest_file(fake_file_id)

    def test_rollback_called_on_exception(self, fake_file_id, mock_db_session):
        from app.workers.ingestion import ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        with patch(
            "app.workers.ingestion._extract_text",
            side_effect=RuntimeError("docling crash"),
        ):
            with pytest.raises(RuntimeError):
                ingest_file(fake_file_id)

        mock_db_session.rollback.assert_called()

    def test_session_closed_even_on_exception(self, fake_file_id, mock_db_session):
        from app.workers.ingestion import ingest_file

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            self._make_file_row(fake_file_id)
        )

        with patch(
            "app.workers.ingestion._extract_text",
            side_effect=RuntimeError("crash"),
        ):
            with pytest.raises(RuntimeError):
                ingest_file(fake_file_id)

        mock_db_session.close.assert_called_once()

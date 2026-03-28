import uuid
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def fake_file_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture()
def mock_embedding_model():
    """
    Returns a mock SentenceTransformer whose encode() produces
    deterministic 384-dim vectors. Patch the global singleton so
    subsequent calls within the same test reuse it.
    """
    import numpy as np

    model = MagicMock()
    model.encode.return_value = np.zeros((1, 384), dtype="float32")
    with patch("app.workers.ingestion._embedding_model", model):
        yield model


@pytest.fixture()
def mock_db_session():
    """
    A lightweight mock of a SQLAlchemy Session. Tests set return values
    on execute().scalar_one_or_none() individually.
    """
    session = MagicMock()
    session.__enter__ = lambda s: s
    session.__exit__ = MagicMock(return_value=False)
    return session


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for download tests."""
    mock_client = MagicMock()
    mock_client.storage.from_.return_value.download.return_value = (
        b"%PDF-1.4 fake content"
    )

    with patch("app.workers.ingestion._get_supabase_client", return_value=mock_client):
        yield mock_client

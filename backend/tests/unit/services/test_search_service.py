from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services import search_service

USER_ID = str(uuid4())
VAULT_ID = str(uuid4())
FILE_ID = str(uuid4())

_RAW_ROW = {
    "id": str(uuid4()),
    "content": "Mitochondria are the powerhouse of the cell.",
    "file_id": FILE_ID,
    "original_name": "biology.pdf",
    "page_number": 3,
    "section_title": "Cell Biology",
    "rrf_score": 0.032,
}


@pytest.mark.asyncio
async def test_search_returns_results():
    db = AsyncMock()
    vault = MagicMock()

    with (
        patch(
            "app.services.search_service.vault_service.get_vault",
            AsyncMock(return_value=vault),
        ),
        patch("app.services.search_service.embed_query", return_value=[0.1] * 384),
        patch(
            "app.services.search_service.hybrid_search",
            AsyncMock(return_value=[_RAW_ROW]),
        ),
    ):
        results = await search_service.search(
            db, VAULT_ID, USER_ID, "powerhouse", top_k=5
        )

    assert len(results) == 1
    assert results[0].content == _RAW_ROW["content"]
    assert results[0].original_name == "biology.pdf"
    assert results[0].page_number == 3


@pytest.mark.asyncio
async def test_search_empty_vault_returns_empty_list():
    db = AsyncMock()

    with (
        patch(
            "app.services.search_service.vault_service.get_vault",
            AsyncMock(return_value=MagicMock()),
        ),
        patch("app.services.search_service.embed_query", return_value=[0.0] * 384),
        patch("app.services.search_service.hybrid_search", AsyncMock(return_value=[])),
    ):
        results = await search_service.search(db, VAULT_ID, USER_ID, "nothing here")

    assert results == []


@pytest.mark.asyncio
async def test_search_vault_not_found_returns_empty_list():
    db = AsyncMock()

    with patch(
        "app.services.search_service.vault_service.get_vault",
        AsyncMock(return_value=None),
    ):
        results = await search_service.search(db, VAULT_ID, USER_ID, "anything")

    assert results == []


@pytest.mark.asyncio
async def test_search_passes_top_k_to_retriever():
    db = AsyncMock()

    with (
        patch(
            "app.services.search_service.vault_service.get_vault",
            AsyncMock(return_value=MagicMock()),
        ),
        patch("app.services.search_service.embed_query", return_value=[0.1] * 384),
        patch(
            "app.services.search_service.hybrid_search", AsyncMock(return_value=[])
        ) as mock_retriever,
    ):
        await search_service.search(db, VAULT_ID, USER_ID, "query", top_k=20)

    _, kwargs = mock_retriever.call_args
    assert kwargs["top_k"] == 20

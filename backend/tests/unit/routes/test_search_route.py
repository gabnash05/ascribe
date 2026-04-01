from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.search import ChunkSearchResult
from tests.unit.conftest import FILE_ID, VAULT_ID

BASE = f"/api/v1/vaults/{VAULT_ID}/search"

_RESULT = ChunkSearchResult(
    content="Mitochondria are the powerhouse of the cell.",
    file_id=FILE_ID,
    original_name="bio.pdf",
    page_number=1,
    section_title="Cells",
    score=0.031,
    importance_score=1.0,
)


@pytest.mark.asyncio
async def test_search_returns_results(client):
    with patch(
        "app.api.v1.search.search_service.search", AsyncMock(return_value=[_RESULT])
    ):
        resp = await client.post(BASE, json={"query": "powerhouse", "top_k": 5})

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["query"] == "powerhouse"
    assert body["results"][0]["content"] == _RESULT.content


@pytest.mark.asyncio
async def test_search_empty_results_is_200_not_404(client):
    with patch("app.api.v1.search.search_service.search", AsyncMock(return_value=[])):
        resp = await client.post(BASE, json={"query": "nothing matches"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_search_validates_query_min_length(client):
    resp = await client.post(BASE, json={"query": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_validates_top_k_bounds(client):
    resp = await client.post(BASE, json={"query": "test", "top_k": 999})
    assert resp.status_code == 422

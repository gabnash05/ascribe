from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.ai import Flashcard, QuizQuestion
from tests.unit.conftest import VAULT_ID

BASE = f"/api/v1/vaults/{VAULT_ID}"

_FLASHCARD = Flashcard(question="What is X?", answer="X is Y.", difficulty="easy")

_QUIZ_QUESTION = QuizQuestion(
    question="What is X?",
    options=["A. P", "B. Q", "C. R", "D. S"],
    correct="A",
    explanation=[
        "A. Correct — P is the answer.",
        "B. Incorrect — Q is unrelated.",
        "C. Incorrect — R is a distractor.",
        "D. Incorrect — S is wrong.",
    ],
)


def _patch_has_content(value: bool):
    return patch(
        "app.api.v1.ai.file_service.vault_has_ready_files",
        AsyncMock(return_value=value),
    )


# ── summarize ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_summarize_200(client):
    with (
        _patch_has_content(True),
        patch(
            "app.api.v1.ai.ai_service.summarize",
            AsyncMock(return_value="## Summary\n- Point."),
        ),
    ):
        resp = await client.post(f"{BASE}/summarize", json={})

    assert resp.status_code == 200
    assert resp.json()["summary"] is not None


@pytest.mark.asyncio
async def test_summarize_422_no_content(client):
    with _patch_has_content(False):
        resp = await client.post(f"{BASE}/summarize", json={})

    assert resp.status_code == 422
    assert "No indexed content" in resp.json()["detail"]


# ── generate-qa ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_qa_200(client):
    with (
        _patch_has_content(True),
        patch(
            "app.api.v1.ai.ai_service.generate_flashcards",
            AsyncMock(return_value=[_FLASHCARD]),
        ),
    ):
        resp = await client.post(f"{BASE}/generate-qa", json={"count": 1})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["flashcards"]) == 1
    assert body["flashcards"][0]["difficulty"] == "easy"


@pytest.mark.asyncio
async def test_generate_qa_422_no_content(client):
    with _patch_has_content(False):
        resp = await client.post(f"{BASE}/generate-qa", json={})

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_generate_qa_validates_count_bounds(client):
    with _patch_has_content(True):
        resp = await client.post(f"{BASE}/generate-qa", json={"count": 0})

    assert resp.status_code == 422


# ── quiz ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_quiz_200(client):
    with (
        _patch_has_content(True),
        patch(
            "app.api.v1.ai.ai_service.generate_quiz",
            AsyncMock(return_value=[_QUIZ_QUESTION]),
        ),
    ):
        resp = await client.post(f"{BASE}/quiz", json={"count": 1})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["quiz"]) == 1
    assert len(body["quiz"][0]["options"]) == 4
    assert len(body["quiz"][0]["explanation"]) == 4


@pytest.mark.asyncio
async def test_generate_quiz_422_no_content(client):
    with _patch_has_content(False):
        resp = await client.post(f"{BASE}/quiz", json={})

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_generate_quiz_validates_count_bounds(client):
    with _patch_has_content(True):
        resp = await client.post(f"{BASE}/quiz", json={"count": 99})

    assert resp.status_code == 422

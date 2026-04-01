from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.ai import Flashcard, QuizQuestion
from app.services import ai_service

USER_ID = str(uuid4())
VAULT_ID = str(uuid4())

_FLASHCARD_DATA = [
    {"question": "What is X?", "answer": "X is Y.", "difficulty": "easy"},
    {
        "question": "Why does A cause B?",
        "answer": "A causes B because of C.",
        "difficulty": "medium",
    },
]

_QUIZ_DATA = [
    {
        "question": "What is the primary reason X occurs?",
        "options": ["A. P", "B. Q", "C. R", "D. S"],
        "correct": "B",
        "explanation": [
            "A. Incorrect — P is unrelated.",
            "B. Correct — Q is the cause.",
            "C. Incorrect — R affects Y.",
            "D. Incorrect — S is conditional.",
        ],
    }
]


# ── summarize ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_summarize_returns_string():
    db = AsyncMock()

    with (
        patch(
            "app.services.ai_service._get_context",
            AsyncMock(return_value="Some content here."),
        ),
        patch(
            "app.services.ai_service._invoke", return_value="## Summary\n- Key point."
        ),
    ):
        result = await ai_service.summarize(db, VAULT_ID, USER_ID)

    assert isinstance(result, str)
    assert "Summary" in result


@pytest.mark.asyncio
async def test_summarize_empty_context_returns_fallback():
    db = AsyncMock()

    with patch("app.services.ai_service._get_context", AsyncMock(return_value="")):
        result = await ai_service.summarize(db, VAULT_ID, USER_ID)

    assert "No content" in result


# ── generate_flashcards ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_flashcards_returns_flashcard_objects():
    db = AsyncMock()

    with (
        patch(
            "app.services.ai_service._get_context", AsyncMock(return_value="Content.")
        ),
        patch(
            "app.services.ai_service._invoke_validated",
            return_value=[Flashcard(**item) for item in _FLASHCARD_DATA],
        ),
    ):
        result = await ai_service.generate_flashcards(db, VAULT_ID, USER_ID, count=2)

    assert len(result) == 2
    assert all(isinstance(f, Flashcard) for f in result)
    assert result[0].difficulty in ("easy", "medium", "hard")


@pytest.mark.asyncio
async def test_generate_flashcards_empty_context_returns_empty():
    db = AsyncMock()

    with patch("app.services.ai_service._get_context", AsyncMock(return_value="   ")):
        result = await ai_service.generate_flashcards(db, VAULT_ID, USER_ID)

    assert result == []


@pytest.mark.asyncio
async def test_generate_flashcards_difficulty_distribution():
    """Verify easy/medium/hard counts are injected into the prompt."""
    db = AsyncMock()

    with (
        patch(
            "app.services.ai_service._get_context", AsyncMock(return_value="Content.")
        ),
        patch(
            "app.services.ai_service._invoke_validated", return_value=[]
        ) as mock_validated,
    ):
        await ai_service.generate_flashcards(db, VAULT_ID, USER_ID, count=10)

    prompt_arg = mock_validated.call_args[0][1]  # second positional arg is prompt
    assert "easy" in prompt_arg
    assert "medium" in prompt_arg
    assert "hard" in prompt_arg


# ── generate_quiz ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_quiz_returns_quiz_question_objects():
    db = AsyncMock()

    with (
        patch(
            "app.services.ai_service._get_context", AsyncMock(return_value="Content.")
        ),
        patch(
            "app.services.ai_service._invoke_validated",
            return_value=[QuizQuestion(**item) for item in _QUIZ_DATA],
        ),
    ):
        result = await ai_service.generate_quiz(db, VAULT_ID, USER_ID, count=1)

    assert len(result) == 1
    assert isinstance(result[0], QuizQuestion)
    assert result[0].correct in ("A", "B", "C", "D")
    assert len(result[0].options) == 4
    assert len(result[0].explanation) == 4


@pytest.mark.asyncio
async def test_generate_quiz_empty_context_returns_empty():
    db = AsyncMock()

    with patch("app.services.ai_service._get_context", AsyncMock(return_value="")):
        result = await ai_service.generate_quiz(db, VAULT_ID, USER_ID)

    assert result == []


# ── _invoke_validated (validation + retry logic) ──────────────────────────────


def test_invoke_validated_passes_on_all_valid():
    valid_data = [
        {
            "question": "What is X exactly?",
            "answer": "X is Y indeed.",
            "difficulty": "easy",
        }
    ]

    with patch("app.services.ai_service._invoke_json", return_value=valid_data):
        result = ai_service._invoke_validated(Flashcard, "prompt", required_count=1)

    assert len(result) == 1
    assert isinstance(result[0], Flashcard)


def test_invoke_validated_retries_on_invalid_items():
    bad_data = [{"question": "Missing answer field"}]
    good_data = [
        {
            "question": "What is X exactly?",
            "answer": "X is Y indeed.",
            "difficulty": "easy",
        }
    ]

    with patch(
        "app.services.ai_service._invoke_json", side_effect=[bad_data, good_data]
    ):
        result = ai_service._invoke_validated(Flashcard, "prompt", required_count=1)

    assert len(result) == 1


def test_invoke_validated_raises_if_still_insufficient_after_retry():
    bad_data = [{"broken": True}]

    with (
        patch("app.services.ai_service._invoke_json", side_effect=[bad_data, bad_data]),
        pytest.raises(ValueError, match="valid Flashcard items"),
    ):
        ai_service._invoke_validated(Flashcard, "prompt", required_count=1)


def test_invoke_validated_trims_overgenerated_results():
    data = [
        {
            "question": f"What is concept number {i}?",
            "answer": "It is a thing.",
            "difficulty": "easy",
        }
        for i in range(5)
    ]

    with patch("app.services.ai_service._invoke_json", return_value=data):
        result = ai_service._invoke_validated(Flashcard, "prompt", required_count=3)

    assert len(result) == 3

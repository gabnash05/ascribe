import json
from functools import lru_cache
from typing import TypeVar
from uuid import UUID

from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.chunk import Chunk
from app.schemas.ai import Flashcard, QuizQuestion
from app.services import search_service

_MAX_CONTEXT_CHARS = 12_000
_BROAD_QUERY = "key concepts definitions important facts"

ModelT = TypeVar("ModelT", Flashcard, QuizQuestion)


@lru_cache(maxsize=1)
def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        api_key=settings.openai_api_key,
    )


# ── context retrieval ─────────────────────────────────────────────────────────


async def _get_context(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
    file_ids: list[UUID] | None,
) -> str:
    if file_ids:
        result = await db.execute(
            select(Chunk.content)
            .where(
                Chunk.file_id.in_([str(fid) for fid in file_ids]),
                Chunk.vault_id == vault_id,
            )
            .order_by(Chunk.file_id, Chunk.chunk_index)
        )
        chunks = [row[0] for row in result.all()]
        context = "\n\n".join(chunks)
    else:
        results = await search_service.search(
            db=db,
            vault_id=vault_id,
            user_id=user_id,
            query=_BROAD_QUERY,
            top_k=30,
        )
        context = "\n\n".join(r.content for r in results)

    return context[:_MAX_CONTEXT_CHARS]


# ── LLM helpers ───────────────────────────────────────────────────────────────


def _invoke(prompt: str) -> str:
    response = _get_llm().invoke(prompt)
    return response.content


def _invoke_json(prompt: str) -> list:
    """
    Call the LLM expecting a JSON array.
    Retries once with an explicit correction instruction on parse failure.
    Raises ValueError if the second attempt also fails.
    """
    raw = _invoke(prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fix_prompt = (
            f"{prompt}\n\n"
            "IMPORTANT: Your previous response could not be parsed as JSON. "
            "Return ONLY a raw JSON array — no markdown code fences, no prose, "
            "no explanation. The very first character of your response must be `[` "
            "and the very last must be `]`."
        )
        raw2 = _invoke(fix_prompt)
        try:
            return json.loads(raw2)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned invalid JSON after retry.") from exc


def _validate_items(
    model_cls: type[ModelT],
    data: list,
) -> tuple[list[ModelT], list[dict]]:
    """
    Validate each raw dict against a Pydantic model individually.

    Returns:
        valid   — successfully constructed model instances
        invalid — raw dicts that failed validation (for use in retry prompts)
    """
    valid: list[ModelT] = []
    invalid: list[dict] = []
    for item in data:
        try:
            valid.append(model_cls(**item))
        except (ValidationError, TypeError):
            invalid.append(item)
    return valid, invalid


def _invoke_validated(
    model_cls: type[ModelT],
    prompt: str,
    required_count: int,
) -> list[ModelT]:
    """
    Call the LLM, parse JSON, then validate every item with Pydantic individually.

    If any items fail validation, retry once — feeding the bad items back to
    the model so it can see exactly what it got wrong. After the retry, keep
    all valid items from the second response.

    Raises ValueError if the final valid count is below required_count.
    Trims to required_count if the model over-generated.
    """
    data = _invoke_json(prompt)
    valid, invalid = _validate_items(model_cls, data)

    if invalid:
        bad_items_json = json.dumps(invalid, indent=2)
        fix_prompt = (
            f"{prompt}\n\n"
            "IMPORTANT: The following items from your previous response failed "
            "schema validation and must be corrected or replaced:\n"
            f"{bad_items_json}\n\n"
            f"Return a complete corrected array of exactly {required_count} items. "
            "Every item must conform strictly to the schema described above."
        )
        data2 = _invoke_json(fix_prompt)
        valid, _ = _validate_items(model_cls, data2)

    if len(valid) < required_count:
        raise ValueError(
            f"Expected {required_count} valid {model_cls.__name__} items after "
            f"validation retry, got {len(valid)}."
        )

    return valid[:required_count]


# ── prompt templates ──────────────────────────────────────────────────────────

_SUMMARIZE_PROMPT = """\
You are an expert study assistant helping a student review their course material.

Your task: write a structured summary of the content below.

RULES:
- Use only information from the provided content. Do not add outside knowledge.
- Organise your output with Markdown headings (##) for each major topic.
- Under each heading, write 2–5 bullet points covering key definitions, \
relationships, processes, or conclusions.
- After all topic sections, add a ## Key Takeaways section with 3–5 \
one-sentence bullets capturing the most important ideas across the whole content.
- Be precise. Prefer specific terms and numbers from the source over vague generalities.
- Do not pad with filler phrases like "this content discusses…".

CONTENT:
{context}
"""

_FLASHCARD_PROMPT = """\
You are an expert study assistant creating flashcards for a student.

Your task: generate exactly {count} flashcard objects from the content below.

QUALITY RULES:
- Vary question types across the deck. Use a mix of:
    • Definition recall    — "What is…" / "Define…"
    • Conceptual reasoning — "Why does…" / "What causes…"
    • Application         — "What would happen if…" / "How would you use…"
    • Comparison          — "What is the difference between X and Y?"
    • Process/sequence    — "What is the first step in…" / "In what order does…"
  No single type should make up more than 40% of the deck.
- Answers must be complete and self-contained in at most 2 sentences. \
A student should be able to learn the core fact from the answer alone.
- Distribute difficulty: roughly {easy} easy, {medium} medium, {hard} hard cards.
- Do not repeat the same concept across multiple cards.
- Do not use yes/no questions.
- Use only information from the provided content.

OUTPUT FORMAT:
Return a raw JSON array. No markdown fences. No prose before or after.
The first character must be `[` and the last must be `]`.
Each element must have exactly these three keys:
  "question"   — a string ending with "?"
  "answer"     — a string of exactly 1–2 sentences
  "difficulty" — exactly one of: "easy", "medium", "hard"

Example of one valid element:
{{"question": "Why does X cause Y under condition Z?", "answer": "X causes Y because …", "difficulty": "medium"}}

CONTENT:
{context}
"""

_QUIZ_PROMPT = """\
You are an expert study assistant creating a multiple-choice quiz for a student.

Your task: generate exactly {count} quiz questions from the content below.

QUALITY RULES:
- Vary question types across the quiz. Use a mix of:
    • Definition/recall    — "What is…" / "Which of the following best defines…"
    • Conceptual reasoning — "Why does…" / "What is the primary cause of…"
    • Application         — "In situation X, what would you do…" / "Which approach is correct when…"
    • Comparison          — "What distinguishes X from Y?"
    • Process/sequence    — "Which step comes after…" / "What is the correct order of…"
  No single type should make up more than 40% of the questions.
- All four options must be plausible; distractors should represent common \
misconceptions or partially-correct statements — not obviously wrong answers.
- Vary which letter (A/B/C/D) is correct across questions; do not cluster \
correct answers on the same letter.
- Each explanation entry must be specific: state WHY the option is correct or \
incorrect in at most 2 sentences, referencing the relevant concept from the content.
- Do not repeat the same concept across multiple questions.
- Use only information from the provided content.

OUTPUT FORMAT:
Return a raw JSON array. No markdown fences. No prose before or after.
The first character must be `[` and the last must be `]`.
Each element must have exactly these four keys:
  "question"    — string
  "options"     — array of exactly 4 strings, formatted as \
["A. <text>", "B. <text>", "C. <text>", "D. <text>"]
  "correct"     — exactly one of: "A", "B", "C", "D"
  "explanation" — array of exactly 4 strings, one per option in the same order \
as "options". Each string explains why that specific option is correct or incorrect.

Example of one valid element:
{{
  "question": "What is the primary reason X occurs?",
  "options": ["A. Because of P", "B. Due to Q", "C. As a result of R", "D. Owing to S"],
  "correct": "B",
  "explanation": [
    "A. Incorrect — P is a consequence of X, not its cause.",
    "B. Correct — Q directly triggers X by …",
    "C. Incorrect — R is unrelated to X; it affects Y instead.",
    "D. Incorrect — S influences X only under condition Z, which is not the general case."
  ]
}}

CONTENT:
{context}
"""


# ── public API ────────────────────────────────────────────────────────────────


async def summarize(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
    file_ids: list[UUID] | None = None,
) -> str:
    context = await _get_context(db, vault_id, user_id, file_ids)
    if not context.strip():
        return "No content available in this vault yet."

    prompt = _SUMMARIZE_PROMPT.format(context=context)
    return _invoke(prompt)


async def generate_flashcards(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
    count: int = 10,
    file_ids: list[UUID] | None = None,
) -> list[Flashcard]:
    context = await _get_context(db, vault_id, user_id, file_ids)
    if not context.strip():
        return []

    base, remainder = divmod(count, 3)
    easy = base + (1 if remainder > 0 else 0)
    medium = base + (1 if remainder > 1 else 0)
    hard = base

    prompt = _FLASHCARD_PROMPT.format(
        count=count,
        easy=easy,
        medium=medium,
        hard=hard,
        context=context,
    )
    return _invoke_validated(Flashcard, prompt, required_count=count)


async def generate_quiz(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
    count: int = 5,
    file_ids: list[UUID] | None = None,
) -> list[QuizQuestion]:
    context = await _get_context(db, vault_id, user_id, file_ids)
    if not context.strip():
        return []

    prompt = _QUIZ_PROMPT.format(count=count, context=context)
    return _invoke_validated(QuizQuestion, prompt, required_count=count)

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.ai import (
    AIResponse,
    Flashcard,
    FlashcardRequest,
    QuizQuestion,
    QuizRequest,
    SummarizeRequest,
)
from app.services import ai_service, file_service

router = APIRouter(prefix="/vaults/{vault_id}", tags=["ai"])

_NO_CONTENT_DETAIL = (
    "No indexed content found. Upload and process files before using AI features."
)


async def _require_ready_content(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
) -> None:
    """Raise 422 if the vault has no ready files."""
    has_content = await file_service.vault_has_ready_files(db, vault_id, user_id)
    if not has_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_NO_CONTENT_DETAIL,
        )


@router.post("/summarize", response_model=AIResponse)
async def summarize(
    vault_id: UUID,
    body: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    # NOTE: Streaming via StreamingResponse + LangChain .stream() is a
    # phase-2 enhancement. For now, await the full response.

    await _require_ready_content(db, str(vault_id), str(current_user))

    summary = await ai_service.summarize(
        db=db,
        vault_id=str(vault_id),
        user_id=str(current_user),
        file_ids=body.file_ids,
    )
    return AIResponse(summary=summary)


@router.post("/generate-qa", response_model=AIResponse)
async def generate_qa(
    vault_id: UUID,
    body: FlashcardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    await _require_ready_content(db, str(vault_id), str(current_user))

    flashcards: list[Flashcard] = await ai_service.generate_flashcards(
        db=db,
        vault_id=str(vault_id),
        user_id=str(current_user),
        count=body.count,
        file_ids=body.file_ids,
    )
    return AIResponse(flashcards=flashcards)


@router.post("/quiz", response_model=AIResponse)
async def generate_quiz(
    vault_id: UUID,
    body: QuizRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    await _require_ready_content(db, str(vault_id), str(current_user))

    questions: list[QuizQuestion] = await ai_service.generate_quiz(
        db=db,
        vault_id=str(vault_id),
        user_id=str(current_user),
        count=body.count,
        file_ids=body.file_ids,
    )
    return AIResponse(quiz=questions)

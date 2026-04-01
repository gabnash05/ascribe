from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SummarizeRequest(BaseModel):
    file_ids: list[UUID] | None = None


class FlashcardRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=50)
    file_ids: list[UUID] | None = None


class Flashcard(BaseModel):
    question: str = Field(..., min_length=10)
    answer: str = Field(..., min_length=5)
    difficulty: Literal["easy", "medium", "hard"]

    @field_validator("question", "answer")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class QuizRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    file_ids: list[UUID] | None = None


class QuizQuestion(BaseModel):
    question: str = Field(..., min_length=10)
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct: Literal["A", "B", "C", "D"]
    explanation: list[str] = Field(..., min_length=4, max_length=4)

    @field_validator("options")
    @classmethod
    def options_must_be_labelled(cls, v: list[str]) -> list[str]:
        labels = ("A. ", "B. ", "C. ", "D. ")
        for option, label in zip(v, labels, strict=False):
            if not option.startswith(label):
                raise ValueError(
                    f"Option must start with '{label}', got: '{option[:8]}'"
                )
        return v

    @field_validator("explanation")
    @classmethod
    def explanation_length_matches_options(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError(
                "explanation must contain exactly 4 entries, one per option."
            )
        return [e.strip() for e in v]


class AIResponse(BaseModel):
    summary: str | None = None
    flashcards: list[Flashcard] | None = None
    quiz: list[QuizQuestion] | None = None

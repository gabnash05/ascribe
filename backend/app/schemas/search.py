from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)


class ChunkSearchResult(BaseModel):
    content: str
    file_id: UUID
    original_name: str
    page_number: int | None
    section_title: str | None
    importance_score: float


class SearchResponse(BaseModel):
    results: list[ChunkSearchResult]
    query: str
    total: int

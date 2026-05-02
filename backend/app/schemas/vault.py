import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VaultCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class VaultUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class VaultResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    thumbnail_url: str | None
    vault_metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VaultViewResponse(VaultResponse):
    """Extended vault response with aggregated counts for the UI."""

    document_count: int = 0
    flashcard_count: int = 0
    quiz_count: int = 0
    last_studied: datetime | None = None


class VaultListResponse(BaseModel):
    items: list[VaultResponse]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool


class VaultViewListResponse(BaseModel):
    items: list[VaultViewResponse]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool

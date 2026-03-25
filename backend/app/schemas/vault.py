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
    vault_metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VaultListResponse(BaseModel):
    vaults: list[VaultResponse]
    total: int

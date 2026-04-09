import uuid
from datetime import datetime

from pydantic import BaseModel

from app.enums import FileStatusEnum, ValidFileTypesEnum


class FileResponse(BaseModel):
    id: uuid.UUID
    vault_id: uuid.UUID
    user_id: uuid.UUID
    original_name: str
    file_type: ValidFileTypesEnum
    mime_type: str | None
    size_bytes: int | None
    page_count: int | None
    status: FileStatusEnum
    error_message: str | None
    total_chunks: int
    total_tokens: int
    file_metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    files: list[FileResponse]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool

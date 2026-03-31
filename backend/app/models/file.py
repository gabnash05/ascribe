import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.enums import FileStatusEnum, ValidFileTypesEnum


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vault_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vaults.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[ValidFileTypesEnum] = mapped_column(
        SAEnum(ValidFileTypesEnum, native_enum=False, length=50),
        nullable=False,
        server_default=ValidFileTypesEnum.TXT.value,
    )
    mime_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[FileStatusEnum] = mapped_column(
        SAEnum(FileStatusEnum, native_enum=False, length=50),
        nullable=False,
        server_default=FileStatusEnum.PROCESSING.value,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_chunks: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    file_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    vault: Mapped["Vault"] = relationship("Vault", back_populates="files")  # noqa: F821
    chunks: Mapped[list["Chunk"]] = relationship(  # noqa: F821
        "Chunk", back_populates="file", cascade="all, delete-orphan", lazy="select"
    )

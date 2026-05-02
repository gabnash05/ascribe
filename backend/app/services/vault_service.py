from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File  # needed for the join
from app.models.vault import Vault
from app.schemas.vault import (
    VaultCreate,
    VaultResponse,
    VaultUpdate,
    VaultViewListResponse,
    VaultViewResponse,
)


async def create_vault(db: AsyncSession, user_id: str, data: VaultCreate) -> Vault:
    vault = Vault(
        user_id=user_id,
        name=data.name,
        description=data.description,
    )
    db.add(vault)
    await db.flush()
    await db.refresh(vault)
    return vault


async def list_vaults(
    db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
) -> VaultViewListResponse:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(Vault).where(Vault.user_id == user_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Vault, func.count(File.id).label("document_count"))
        .outerjoin(File, File.vault_id == Vault.id)
        .where(Vault.user_id == user_id)
        .group_by(Vault.id)
        .order_by(Vault.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    vaults = [
        VaultViewResponse(
            **VaultResponse.model_validate(vault).model_dump(),
            document_count=document_count,
            flashcard_count=0,  # TODO: join flashcards table
            quiz_count=0,  # TODO: join quizzes table
            last_studied=None,  # TODO: join study_sessions table
            thumbnail=None,
        )
        for vault, document_count in rows
    ]

    return VaultViewListResponse(
        items=vaults,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        has_next=offset + page_size < total,
        has_prev=page > 1,
    )


async def get_vault(db: AsyncSession, vault_id: str, user_id: str) -> Vault | None:
    result = await db.execute(
        select(Vault).where(Vault.id == vault_id, Vault.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_vault(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
    data: VaultUpdate,
) -> Vault | None:
    vault = await get_vault(db, vault_id, user_id)
    if vault is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vault, field, value)

    await db.flush()
    await db.refresh(vault)
    return vault


async def delete_vault(db: AsyncSession, vault_id: str, user_id: str) -> bool:
    vault = await get_vault(db, vault_id, user_id)
    if vault is None:
        return False

    await db.delete(vault)
    await db.flush()
    return True

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vault import Vault
from app.schemas.vault import VaultCreate, VaultListResponse, VaultResponse, VaultUpdate


async def create_vault(
    db: AsyncSession, user_id: str, data: VaultCreate
) -> VaultResponse:
    vault = Vault(
        user_id=user_id,
        name=data.name,
        description=data.description,
    )
    db.add(vault)
    await db.flush()
    await db.refresh(vault)
    return VaultResponse.model_validate(vault)


async def list_vaults(
    db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
) -> VaultListResponse:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(Vault).where(Vault.user_id == user_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Vault)
        .where(Vault.user_id == user_id)
        .order_by(Vault.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    vaults = list(result.scalars().all())

    return VaultListResponse(
        vaults=[VaultResponse.model_validate(v) for v in vaults],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        has_next=offset + page_size < total,
        has_prev=page > 1,
    )


async def get_vault(
    db: AsyncSession, vault_id: str, user_id: str
) -> VaultResponse | None:
    result = await db.execute(
        select(Vault).where(Vault.id == vault_id, Vault.user_id == user_id)
    )
    vault = result.scalar_one_or_none()
    return VaultResponse.model_validate(vault) if vault else None


async def update_vault(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
    data: VaultUpdate,
) -> VaultResponse | None:
    vault = await get_vault(db, vault_id, user_id)
    if vault is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vault, field, value)

    await db.flush()
    await db.refresh(vault)
    return VaultResponse.model_validate(vault)


async def delete_vault(db: AsyncSession, vault_id: str, user_id: str) -> bool:
    vault = await get_vault(db, vault_id, user_id)
    if vault is None:
        return False

    await db.delete(vault)
    await db.flush()
    return True

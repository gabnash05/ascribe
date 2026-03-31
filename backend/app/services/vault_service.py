from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vault import Vault
from app.schemas.vault import VaultCreate, VaultUpdate


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


async def list_vaults(db: AsyncSession, user_id: str) -> list[Vault]:
    result = await db.execute(
        select(Vault).where(Vault.user_id == user_id).order_by(Vault.created_at.desc())
    )
    return list(result.scalars().all())


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

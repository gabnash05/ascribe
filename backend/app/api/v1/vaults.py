from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.vault import VaultCreate, VaultResponse, VaultUpdate
from app.services import vault_service

router = APIRouter(prefix="/vaults", tags=["vaults"])


@router.post("", response_model=VaultResponse, status_code=status.HTTP_201_CREATED)
async def create_vault(
    data: VaultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    vault = await vault_service.create_vault(db, str(current_user), data)
    await db.commit()
    await db.refresh(vault)
    return vault


@router.get("", response_model=list[VaultResponse])
async def list_vaults(
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    return await vault_service.list_vaults(db, str(current_user))


@router.get("/{vault_id}", response_model=VaultResponse)
async def get_vault(
    vault_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    vault = await vault_service.get_vault(db, str(vault_id), str(current_user))
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found"
        )
    return vault


@router.put("/{vault_id}", response_model=VaultResponse)
async def update_vault(
    vault_id: UUID,
    data: VaultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    vault = await vault_service.update_vault(db, str(vault_id), str(current_user), data)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found"
        )
    await db.commit()
    await db.refresh(vault)
    return vault


@router.delete("/{vault_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vault(
    vault_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    deleted = await vault_service.delete_vault(db, str(vault_id), str(current_user))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found"
        )
    await db.commit()

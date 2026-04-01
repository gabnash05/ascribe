from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from app.core.clients import get_supabase
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.file import FileResponse
from app.services import file_service

router = APIRouter(prefix="/vaults/{vault_id}/files", tags=["files"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    vault_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    supabase: Client = Depends(get_supabase),
    current_user: UUID = Depends(get_current_user),
):
    try:
        record = await file_service.upload_file(
            db=db,
            supabase_client=supabase,
            vault_id=str(vault_id),
            user_id=str(current_user),
            file=file,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    await db.commit()
    await db.refresh(record)
    return {"file_id": str(record.id), "status": record.status}


@router.get("", response_model=list[FileResponse])
async def list_files(
    vault_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    try:
        return await file_service.list_files(db, str(vault_id), str(current_user))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    vault_id: UUID,
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    record = await file_service.get_file(
        db, str(file_id), str(vault_id), str(current_user)
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return record


@router.get("/{file_id}/status")
async def get_file_status(
    vault_id: UUID,
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    result = await file_service.get_file_status(
        db, str(file_id), str(vault_id), str(current_user)
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return {
        "file_id": str(file_id),
        "status": result["status"],
        "total_chunks": result["total_chunks"],
        "error_message": result["error_message"],
    }


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    vault_id: UUID,
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    supabase: Client = Depends(get_supabase),
    current_user: UUID = Depends(get_current_user),
):
    deleted = await file_service.delete_file(
        db=db,
        supabase_client=supabase,
        file_id=str(file_id),
        vault_id=str(vault_id),
        user_id=str(current_user),
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    await db.commit()

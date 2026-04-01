from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.search import SearchRequest, SearchResponse
from app.services import search_service

router = APIRouter(prefix="/vaults/{vault_id}", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    vault_id: UUID,
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    results = await search_service.search(
        db=db,
        vault_id=str(vault_id),
        user_id=str(current_user),
        query=body.query,
        top_k=body.top_k,
    )
    return SearchResponse(results=results, query=body.query, total=len(results))

from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.embedder import embed_query
from app.pipeline.retriever import hybrid_search
from app.schemas.search import ChunkSearchResult
from app.services import vault_service


async def search(
    db: AsyncSession,
    vault_id: str,
    user_id: str,
    query: str,
    top_k: int = 10,
) -> list[ChunkSearchResult]:
    vault = await vault_service.get_vault(db, vault_id, user_id)
    if vault is None:
        return []

    query_vec: list[float] = embed_query(query)

    raw_results: list[dict] = await hybrid_search(
        db=db,
        vault_id=vault_id,
        query_vec=query_vec,
        query_text=query,
        top_k=top_k,
    )

    results = [
        ChunkSearchResult(
            content=row["content"],
            file_id=row["file_id"],
            original_name=row["original_name"],
            page_number=row.get("page_number"),
            section_title=row.get("section_title"),
            importance_score=float(row["rrf_score"]),
        )
        for row in raw_results
    ]

    return results

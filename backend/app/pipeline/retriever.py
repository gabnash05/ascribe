from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_HYBRID_SEARCH_SQL = """
WITH semantic AS (
    SELECT
        id, content, file_id, page_number, section_title,
        (1 - (embedding <=> :query_vec::vector)) AS semantic_score
    FROM chunks
    WHERE vault_id = :vault_id
    ORDER BY embedding <=> :query_vec::vector
    LIMIT :top_k
),
keyword AS (
    SELECT
        id, content, file_id, page_number, section_title,
        ts_rank(ts_vector, plainto_tsquery('english', :query_text)) AS keyword_score
    FROM chunks
    WHERE vault_id = :vault_id
      AND ts_vector @@ plainto_tsquery('english', :query_text)
    ORDER BY keyword_score DESC
    LIMIT :top_k
),
merged AS (
    SELECT
        COALESCE(s.id, k.id)                       AS id,
        COALESCE(s.content, k.content)             AS content,
        COALESCE(s.file_id, k.file_id)             AS file_id,
        COALESCE(s.page_number, k.page_number)     AS page_number,
        COALESCE(s.section_title, k.section_title) AS section_title,
        (1.0 / (60 + COALESCE(s_rank.rank, 999))) +
        (1.0 / (60 + COALESCE(k_rank.rank, 999))) AS rrf_score
    FROM semantic s
    FULL OUTER JOIN keyword k ON s.id = k.id
    LEFT JOIN (
        SELECT id, ROW_NUMBER() OVER (ORDER BY semantic_score DESC) AS rank
        FROM semantic
    ) s_rank ON s_rank.id = COALESCE(s.id, k.id)
    LEFT JOIN (
        SELECT id, ROW_NUMBER() OVER (ORDER BY keyword_score DESC) AS rank
        FROM keyword
    ) k_rank ON k_rank.id = COALESCE(s.id, k.id)
)
SELECT m.id, m.content, m.file_id, m.page_number, m.section_title,
       m.rrf_score, f.original_name
FROM merged m
JOIN files f ON f.id = m.file_id
ORDER BY rrf_score DESC
LIMIT :top_k;
"""


async def hybrid_search(
    db: AsyncSession,
    vault_id: str,
    query_vec: list[float],
    query_text: str,
    top_k: int = 10,
) -> list[dict]:
    """
    Run hybrid semantic + keyword search against the chunks table.

    Returns a list of dicts with keys:
        id, content, file_id, page_number, section_title,
        original_name, rrf_score

    Returns an empty list when the vault has no chunks — never raises.
    """
    result = await db.execute(
        text(_HYBRID_SEARCH_SQL),
        {
            "query_vec": str(query_vec),
            "query_text": query_text,
            "vault_id": vault_id,
            "top_k": top_k,
        },
    )
    rows = result.mappings().all()
    return [dict(row) for row in rows]

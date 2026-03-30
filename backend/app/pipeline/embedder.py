from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings

_BGE_QUERY_PREFIX = "Represent this sentence for searching: "


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    model = SentenceTransformer(
        settings.embedding_model, cache_folder=settings.embedding_cache_dir
    )
    return model


def embed_query(query: str) -> list[float]:
    """Embed a single query string with the BGE asymmetric-retrieval prefix."""
    model = _get_model()
    prefixed_query = _BGE_QUERY_PREFIX + query
    embedding = model.encode(
        prefixed_query, normalize_embeddings=True, show_progress_bar=False
    )
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts without any prefix."""
    model = _get_model()
    embeddings = model.encode(
        texts, normalize_embeddings=True, show_progress_bar=False, batch_size=64
    )
    return embeddings.tolist()

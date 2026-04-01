import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import ai, files, search, vaults

from .core.config import settings
from .core.database import engine
from .core.security import get_current_user
from .pipeline.embedder import embed_query

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""

    try:
        logger.info("Warming up embedding model...")
        await asyncio.to_thread(embed_query, "warmup")
        logger.info("Embedding model ready")
    except Exception as e:
        logger.error(f"Failed to warm embedding model: {e}")

    yield

    logger.info("Shutting down...")
    await engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title="AScribe API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(vaults.router, prefix="/api/v1", tags=["vaults"])
app.include_router(files.router, prefix="/api/v1", tags=["files"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(ai.router, prefix="/api/v1", tags=["ai"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/test-auth")
async def test_auth(user: str = Depends(get_current_user)):
    return {"user": user}

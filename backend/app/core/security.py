import asyncio
import time
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

from .config import settings

bearer_scheme = HTTPBearer()

_jwks_cache: dict | None = None
_jwks_expiry: float = 0
_JWKS_TTL = 3600  # 1 hour
_jwks_lock = asyncio.Lock()


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_expiry

    now = time.time()

    if _jwks_cache is not None and now <= _jwks_expiry:
        return _jwks_cache

    async with _jwks_lock:
        now = time.time()
        if _jwks_cache is not None and now <= _jwks_expiry:
            return _jwks_cache

        try:
            url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                _jwks_cache = resp.json()
                _jwks_expiry = now + _JWKS_TTL
                return _jwks_cache

        except httpx.HTTPError as err:
            if _jwks_cache is not None:
                return _jwks_cache

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch JWKS from authentication service",
            ) from err

        except Exception as err:
            if _jwks_cache is not None:
                return _jwks_cache

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            ) from err


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> str:
    token = credentials.credentials

    try:
        jwks = await _get_jwks()

        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")
        alg = headers.get("alg", "ES256")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
            )

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature",
            )

        public_key = jwk.construct(key)

        allowed_algorithms = [alg] if alg else ["RS256", "ES256", "HS256"]

        payload = jwt.decode(
            token,
            public_key,
            algorithms=allowed_algorithms,
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
        )

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier",
            )

        return user_id

    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from err

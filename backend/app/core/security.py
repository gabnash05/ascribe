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


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_expiry

    now = time.time()
    if _jwks_cache is None or now > _jwks_expiry:
        url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_expiry = now + _JWKS_TTL

    return _jwks_cache


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
        if not kid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        public_key = jwk.construct(key)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
        )

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return user_id

    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from err

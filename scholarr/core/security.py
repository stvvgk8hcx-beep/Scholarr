"""Security utilities for Scholarr."""

from fastapi import HTTPException, Header, status
from typing import Optional

from scholarr.core.config import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from request header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
        )

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return x_api_key

"""Authentication and authorization for Scholarr."""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from scholarr.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """Verify API key from request header.

    Args:
        api_key: API key from X-API-Key header.

    Returns:
        str: The verified API key.

    Raises:
        HTTPException: If API key is missing or invalid.
    """
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API key",
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key


def generate_api_key() -> str:
    """Generate a secure random API key.

    Returns:
        str: A URL-safe base64 encoded random string.
    """
    return secrets.token_urlsafe(32)

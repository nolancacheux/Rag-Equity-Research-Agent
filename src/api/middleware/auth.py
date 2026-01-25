"""API Key authentication middleware."""

import os
from collections.abc import Callable
from functools import wraps

from fastapi import HTTPException, Request, status


def get_api_key() -> str | None:
    """Get API key from environment."""
    return os.environ.get("API_SECRET_KEY")


async def verify_api_key(request: Request) -> None:
    """Verify API key from request header.

    Args:
        request: FastAPI request object.

    Raises:
        HTTPException: If API key is missing or invalid.
    """
    api_key = get_api_key()

    # If no API key configured, skip auth (dev mode)
    if not api_key:
        return

    # Check header
    request_key = request.headers.get("X-API-Key")
    if not request_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
        )

    if request_key != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


def require_api_key(func: Callable) -> Callable:
    """Decorator to require API key for endpoint."""

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        await verify_api_key(request)
        return await func(request, *args, **kwargs)

    return wrapper

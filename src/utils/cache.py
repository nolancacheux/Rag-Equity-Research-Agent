"""In-memory caching utilities for API responses."""

import hashlib
import json
import time
from functools import lru_cache
from typing import Any

import structlog

from src.config import get_settings

logger = structlog.get_logger()


class MemoryCache:
    """Simple in-memory caching for API responses."""

    def __init__(self, default_ttl: int = 3600) -> None:
        """Initialize memory cache.

        Args:
            default_ttl: Default TTL in seconds
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    @staticmethod
    def _make_key(prefix: str, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from prefix and arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"

    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        now = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if exp < now]
        for key in expired:
            del self._cache[key]

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        self._cleanup_expired()

        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > time.time():
                logger.debug("cache_hit", key=key)
                return value
            else:
                del self._cache[key]

        logger.debug("cache_miss", key=key)
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not specified)

        Returns:
            True if successful
        """
        ttl = ttl or self._default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
        logger.debug("cache_set", key=key, ttl=ttl)
        return True

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_delete", key=key)
            return True
        return False

    @property
    def is_connected(self) -> bool:
        """Always connected for memory cache."""
        return True


# Backwards compatibility aliases
RedisCache = MemoryCache


@lru_cache
def get_cache() -> MemoryCache:
    """Get cached memory cache instance."""
    settings = get_settings()
    return MemoryCache(default_ttl=settings.cache_ttl_seconds)

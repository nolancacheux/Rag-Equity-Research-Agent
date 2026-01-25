"""Redis caching utilities for API responses."""

import hashlib
import json
from functools import lru_cache
from typing import Any

import redis
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class RedisCache:
    """Redis-based caching for API responses."""

    def __init__(self, url: str, default_ttl: int = 3600) -> None:
        """Initialize Redis cache.

        Args:
            url: Redis connection URL
            default_ttl: Default TTL in seconds
        """
        self._client: redis.Redis | None = None
        self._url = url
        self._default_ttl = default_ttl
        self._connected = False

    def _connect(self) -> redis.Redis | None:
        """Establish Redis connection with error handling."""
        if self._client is not None:
            return self._client

        try:
            self._client = redis.from_url(
                self._url,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            self._client.ping()
            self._connected = True
            logger.info("redis_connected", url=self._url)
            return self._client
        except redis.ConnectionError as e:
            logger.warning("redis_connection_failed", error=str(e))
            self._connected = False
            return None

    @staticmethod
    def _make_key(prefix: str, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from prefix and arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        client = self._connect()
        if client is None:
            return None

        try:
            value = client.get(key)
            if value:
                logger.debug("cache_hit", key=key)
                return json.loads(value)
            logger.debug("cache_miss", key=key)
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning("cache_get_error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (uses default if not specified)

        Returns:
            True if successful, False otherwise
        """
        client = self._connect()
        if client is None:
            return False

        try:
            ttl = ttl or self._default_ttl
            client.setex(key, ttl, json.dumps(value))
            logger.debug("cache_set", key=key, ttl=ttl)
            return True
        except (redis.RedisError, TypeError) as e:
            logger.warning("cache_set_error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        client = self._connect()
        if client is None:
            return False

        try:
            client.delete(key)
            logger.debug("cache_delete", key=key)
            return True
        except redis.RedisError as e:
            logger.warning("cache_delete_error", key=key, error=str(e))
            return False

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected


@lru_cache
def get_cache() -> RedisCache:
    """Get cached Redis cache instance."""
    settings = get_settings()
    return RedisCache(
        url=settings.redis_url,
        default_ttl=settings.cache_ttl_seconds,
    )

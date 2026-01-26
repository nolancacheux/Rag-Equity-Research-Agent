"""Tests for utility modules."""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch


class TestMemoryCache:
    """Tests for MemoryCache class."""

    def test_init(self):
        """Test cache initialization."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache(default_ttl=3600)
        assert cache._default_ttl == 3600
        assert cache._cache == {}

    def test_make_key(self):
        """Test cache key generation."""
        from src.utils.cache import MemoryCache

        key1 = MemoryCache._make_key("prefix", "arg1", kwarg1="value1")
        key2 = MemoryCache._make_key("prefix", "arg1", kwarg1="value1")
        key3 = MemoryCache._make_key("prefix", "arg2", kwarg1="value1")

        assert key1 == key2  # Same args = same key
        assert key1 != key3  # Different args = different key
        assert key1.startswith("prefix:")

    def test_set_and_get(self):
        """Test basic set and get operations."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache(default_ttl=3600)
        
        result = cache.set("test_key", {"data": "value"})
        assert result is True
        
        value = cache.get("test_key")
        assert value == {"data": "value"}

    def test_get_miss(self):
        """Test cache miss."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_get_expired(self):
        """Test expired cache entry."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache(default_ttl=1)
        cache.set("test_key", {"data": "value"}, ttl=0)  # Immediate expiry
        
        # Wait a bit for expiry
        time.sleep(0.1)
        
        result = cache.get("test_key")
        assert result is None

    def test_set_custom_ttl(self):
        """Test cache set with custom TTL."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache(default_ttl=3600)
        cache.set("test_key", {"data": "value"}, ttl=7200)
        
        value, expiry = cache._cache["test_key"]
        assert value == {"data": "value"}
        # Expiry should be ~7200 seconds in the future
        assert expiry > time.time() + 7000

    def test_delete_existing(self):
        """Test deleting existing key."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache()
        cache.set("test_key", "value")
        
        result = cache.delete("test_key")
        assert result is True
        assert cache.get("test_key") is None

    def test_delete_nonexistent(self):
        """Test deleting nonexistent key."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache()
        result = cache.delete("nonexistent")
        assert result is False

    def test_is_connected(self):
        """Test is_connected property (always True for memory cache)."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache()
        assert cache.is_connected is True

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        from src.utils.cache import MemoryCache

        cache = MemoryCache()
        
        # Add entries with different expiries
        cache._cache["expired"] = ("value", time.time() - 10)  # Already expired
        cache._cache["valid"] = ("value", time.time() + 3600)  # Still valid
        
        cache._cleanup_expired()
        
        assert "expired" not in cache._cache
        assert "valid" in cache._cache


class TestGetCache:
    """Tests for get_cache function."""

    def test_get_cache(self):
        """Test get_cache singleton."""
        from src.utils.cache import get_cache

        # Clear the lru_cache
        get_cache.cache_clear()

        cache1 = get_cache()
        cache2 = get_cache()

        # Should return same instance (cached)
        assert cache1 is cache2


class TestRedisBackwardsCompatibility:
    """Test backwards compatibility alias."""

    def test_redis_cache_alias(self):
        """Test that RedisCache is aliased to MemoryCache."""
        from src.utils.cache import RedisCache, MemoryCache

        assert RedisCache is MemoryCache


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init(self):
        """Test rate limiter initialization."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=10, period_seconds=60)

        assert limiter._max_requests == 10
        assert limiter._period == 60

    def test_remaining_full(self):
        """Test remaining when no requests made."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=10, period_seconds=60)
        remaining = limiter.remaining("test")

        assert remaining == 10

    def test_remaining_after_requests(self):
        """Test remaining after some requests."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=10, period_seconds=60)

        # Make some requests
        for _ in range(3):
            limiter.acquire_sync("test")

        remaining = limiter.remaining("test")
        assert remaining == 7

    def test_acquire_sync_success(self):
        """Test synchronous acquire."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=5, period_seconds=60)

        # Should acquire without waiting
        start = time.time()
        for _ in range(5):
            limiter.acquire_sync("test")
        elapsed = time.time() - start

        assert elapsed < 1  # Should be near-instant

    def test_acquire_sync_rate_limited(self):
        """Test synchronous acquire with rate limiting."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=2, period_seconds=0.5)

        # Fill the bucket
        limiter.acquire_sync("test")
        limiter.acquire_sync("test")

        # This should wait
        start = time.time()
        limiter.acquire_sync("test")
        elapsed = time.time() - start

        assert elapsed >= 0.4  # Should have waited

    @pytest.mark.asyncio
    async def test_acquire_async_success(self):
        """Test async acquire."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=5, period_seconds=60)

        # Should acquire without waiting
        start = time.time()
        for _ in range(5):
            await limiter.acquire("test")
        elapsed = time.time() - start

        assert elapsed < 1

    @pytest.mark.asyncio
    async def test_acquire_async_rate_limited(self):
        """Test async acquire with rate limiting."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=2, period_seconds=0.5)

        # Fill the bucket
        await limiter.acquire("test")
        await limiter.acquire("test")

        # This should wait
        start = time.time()
        await limiter.acquire("test")
        elapsed = time.time() - start

        assert elapsed >= 0.4

    def test_cleanup_old_requests(self):
        """Test that old requests are cleaned up."""
        from src.utils.rate_limiter import RateLimiter, RateLimitState

        limiter = RateLimiter(requests_per_period=5, period_seconds=1)

        # Add old requests
        state = limiter._states["test"]
        state.requests = [time.time() - 2, time.time() - 1.5, time.time()]  # First two are old

        limiter._cleanup_old_requests(state)

        assert len(state.requests) == 1  # Only the recent one remains

    def test_multiple_sources(self):
        """Test rate limiting with multiple sources."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_period=2, period_seconds=60)

        # Each source has its own bucket
        limiter.acquire_sync("source1")
        limiter.acquire_sync("source1")
        limiter.acquire_sync("source2")
        limiter.acquire_sync("source2")

        assert limiter.remaining("source1") == 0
        assert limiter.remaining("source2") == 0


class TestPreConfiguredLimiters:
    """Tests for pre-configured rate limiters."""

    def test_yfinance_limiter(self):
        """Test yfinance limiter configuration."""
        from src.utils.rate_limiter import yfinance_limiter

        assert yfinance_limiter._max_requests == 5
        assert yfinance_limiter._period == 1

    def test_sec_limiter(self):
        """Test SEC limiter configuration."""
        from src.utils.rate_limiter import sec_limiter

        assert sec_limiter._max_requests == 10
        assert sec_limiter._period == 1

    def test_search_limiter(self):
        """Test search limiter configuration."""
        from src.utils.rate_limiter import search_limiter

        assert search_limiter._max_requests == 1
        assert search_limiter._period == 2

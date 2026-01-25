"""Tests for utility modules."""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch


class TestRedisCache:
    """Tests for RedisCache class."""

    @patch("src.utils.cache.redis.from_url")
    def test_connect_success(self, mock_from_url):
        """Test successful Redis connection."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        cache = RedisCache("redis://localhost:6379", default_ttl=3600)
        client = cache._connect()

        assert client is not None
        assert cache._connected is True

    @patch("src.utils.cache.redis.from_url")
    def test_connect_failure(self, mock_from_url):
        """Test Redis connection failure."""
        import redis
        from src.utils.cache import RedisCache

        mock_from_url.side_effect = redis.ConnectionError("Connection refused")

        cache = RedisCache("redis://localhost:6379")
        client = cache._connect()

        assert client is None
        assert cache._connected is False

    @patch("src.utils.cache.redis.from_url")
    def test_connect_cached(self, mock_from_url):
        """Test that connection is reused."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        cache = RedisCache("redis://localhost:6379")
        cache._connect()
        cache._connect()

        # Should only connect once
        assert mock_from_url.call_count == 1

    def test_make_key(self):
        """Test cache key generation."""
        from src.utils.cache import RedisCache

        key1 = RedisCache._make_key("prefix", "arg1", kwarg1="value1")
        key2 = RedisCache._make_key("prefix", "arg1", kwarg1="value1")
        key3 = RedisCache._make_key("prefix", "arg2", kwarg1="value1")

        assert key1 == key2  # Same args = same key
        assert key1 != key3  # Different args = different key
        assert key1.startswith("prefix:")

    @patch("src.utils.cache.redis.from_url")
    def test_get_success(self, mock_from_url):
        """Test successful cache get."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.get.return_value = '{"key": "value"}'

        cache = RedisCache("redis://localhost:6379")
        result = cache.get("test_key")

        assert result == {"key": "value"}

    @patch("src.utils.cache.redis.from_url")
    def test_get_miss(self, mock_from_url):
        """Test cache miss."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.get.return_value = None

        cache = RedisCache("redis://localhost:6379")
        result = cache.get("test_key")

        assert result is None

    @patch("src.utils.cache.redis.from_url")
    def test_get_error(self, mock_from_url):
        """Test cache get error handling."""
        import redis
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.get.side_effect = redis.RedisError("Error")

        cache = RedisCache("redis://localhost:6379")
        result = cache.get("test_key")

        assert result is None

    @patch("src.utils.cache.redis.from_url")
    def test_get_json_error(self, mock_from_url):
        """Test cache get with invalid JSON."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.get.return_value = "invalid json {"

        cache = RedisCache("redis://localhost:6379")
        result = cache.get("test_key")

        assert result is None

    @patch("src.utils.cache.redis.from_url")
    def test_get_no_connection(self, mock_from_url):
        """Test cache get with no connection."""
        import redis
        from src.utils.cache import RedisCache

        mock_from_url.side_effect = redis.ConnectionError()

        cache = RedisCache("redis://localhost:6379")
        result = cache.get("test_key")

        assert result is None

    @patch("src.utils.cache.redis.from_url")
    def test_set_success(self, mock_from_url):
        """Test successful cache set."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        cache = RedisCache("redis://localhost:6379", default_ttl=3600)
        result = cache.set("test_key", {"data": "value"})

        assert result is True
        mock_client.setex.assert_called_once()

    @patch("src.utils.cache.redis.from_url")
    def test_set_custom_ttl(self, mock_from_url):
        """Test cache set with custom TTL."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        cache = RedisCache("redis://localhost:6379", default_ttl=3600)
        cache.set("test_key", {"data": "value"}, ttl=7200)

        mock_client.setex.assert_called_with("test_key", 7200, '{"data": "value"}')

    @patch("src.utils.cache.redis.from_url")
    def test_set_error(self, mock_from_url):
        """Test cache set error handling."""
        import redis
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.setex.side_effect = redis.RedisError("Error")

        cache = RedisCache("redis://localhost:6379")
        result = cache.set("test_key", {"data": "value"})

        assert result is False

    @patch("src.utils.cache.redis.from_url")
    def test_set_no_connection(self, mock_from_url):
        """Test cache set with no connection."""
        import redis
        from src.utils.cache import RedisCache

        mock_from_url.side_effect = redis.ConnectionError()

        cache = RedisCache("redis://localhost:6379")
        result = cache.set("test_key", {"data": "value"})

        assert result is False

    @patch("src.utils.cache.redis.from_url")
    def test_delete_success(self, mock_from_url):
        """Test successful cache delete."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        cache = RedisCache("redis://localhost:6379")
        result = cache.delete("test_key")

        assert result is True
        mock_client.delete.assert_called_with("test_key")

    @patch("src.utils.cache.redis.from_url")
    def test_delete_error(self, mock_from_url):
        """Test cache delete error handling."""
        import redis
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.delete.side_effect = redis.RedisError("Error")

        cache = RedisCache("redis://localhost:6379")
        result = cache.delete("test_key")

        assert result is False

    @patch("src.utils.cache.redis.from_url")
    def test_delete_no_connection(self, mock_from_url):
        """Test cache delete with no connection."""
        import redis
        from src.utils.cache import RedisCache

        mock_from_url.side_effect = redis.ConnectionError()

        cache = RedisCache("redis://localhost:6379")
        result = cache.delete("test_key")

        assert result is False

    @patch("src.utils.cache.redis.from_url")
    def test_is_connected(self, mock_from_url):
        """Test is_connected property."""
        from src.utils.cache import RedisCache

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        cache = RedisCache("redis://localhost:6379")
        assert cache.is_connected is False

        cache._connect()
        assert cache.is_connected is True


class TestGetCache:
    """Tests for get_cache function."""

    @patch("src.utils.cache.RedisCache")
    @patch("src.utils.cache.get_settings")
    def test_get_cache(self, mock_settings, mock_cache_class):
        """Test get_cache singleton."""
        from src.utils.cache import get_cache

        # Clear the lru_cache
        get_cache.cache_clear()

        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379"
        mock_settings_obj.cache_ttl_seconds = 3600
        mock_settings.return_value = mock_settings_obj

        cache1 = get_cache()
        cache2 = get_cache()

        # Should return same instance (cached)
        assert cache1 is cache2


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

"""Rate limiting utilities for external API calls."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


@dataclass
class RateLimitState:
    """State for a rate limiter."""

    requests: list[float] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RateLimiter:
    """Token bucket rate limiter for API calls.

    Implements a sliding window rate limiter that tracks requests
    per source (e.g., different APIs have different limits).
    """

    def __init__(self, requests_per_period: int = 100, period_seconds: int = 60) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_period: Max requests allowed per period
            period_seconds: Time period in seconds
        """
        self._max_requests = requests_per_period
        self._period = period_seconds
        self._states: dict[str, RateLimitState] = defaultdict(RateLimitState)

    def _cleanup_old_requests(self, state: RateLimitState) -> None:
        """Remove requests outside the current window."""
        cutoff = time.time() - self._period
        state.requests = [t for t in state.requests if t > cutoff]

    async def acquire(self, source: str = "default") -> None:
        """Acquire a rate limit slot, waiting if necessary.

        Args:
            source: Identifier for the rate limit bucket (e.g., "yfinance", "sec")
        """
        state = self._states[source]

        async with state.lock:
            while True:
                self._cleanup_old_requests(state)

                if len(state.requests) < self._max_requests:
                    state.requests.append(time.time())
                    logger.debug(
                        "rate_limit_acquired",
                        source=source,
                        current=len(state.requests),
                        max=self._max_requests,
                    )
                    return

                # Calculate wait time until oldest request expires
                oldest = min(state.requests)
                wait_time = oldest + self._period - time.time()

                if wait_time > 0:
                    logger.info(
                        "rate_limit_waiting",
                        source=source,
                        wait_seconds=round(wait_time, 2),
                    )
                    await asyncio.sleep(wait_time)

    def acquire_sync(self, source: str = "default") -> None:
        """Synchronous version of acquire for non-async contexts.

        Args:
            source: Identifier for the rate limit bucket
        """
        state = self._states[source]

        while True:
            self._cleanup_old_requests(state)

            if len(state.requests) < self._max_requests:
                state.requests.append(time.time())
                return

            oldest = min(state.requests)
            wait_time = oldest + self._period - time.time()

            if wait_time > 0:
                logger.info(
                    "rate_limit_waiting_sync",
                    source=source,
                    wait_seconds=round(wait_time, 2),
                )
                time.sleep(wait_time)

    def remaining(self, source: str = "default") -> int:
        """Get remaining requests in current window.

        Args:
            source: Identifier for the rate limit bucket

        Returns:
            Number of remaining requests
        """
        state = self._states[source]
        self._cleanup_old_requests(state)
        return max(0, self._max_requests - len(state.requests))


# Pre-configured rate limiters for different APIs
yfinance_limiter = RateLimiter(requests_per_period=5, period_seconds=1)  # 5 req/s
sec_limiter = RateLimiter(requests_per_period=10, period_seconds=1)  # 10 req/s
search_limiter = RateLimiter(requests_per_period=1, period_seconds=2)  # 0.5 req/s

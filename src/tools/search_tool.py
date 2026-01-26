"""DuckDuckGo search tool for news and sentiment."""

from dataclasses import dataclass
from typing import Any

import structlog
from duckduckgo_search import DDGS
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.cache import MemoryCache, get_cache
from src.utils.rate_limiter import search_limiter

logger = structlog.get_logger()


@dataclass
class SearchResult:
    """Search result from DuckDuckGo."""

    title: str
    url: str
    snippet: str
    source: str | None
    published: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "published": self.published,
        }


@dataclass
class NewsResult:
    """News article from DuckDuckGo News."""

    title: str
    url: str
    snippet: str
    source: str
    date: str
    image: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "date": self.date,
            "image": self.image,
        }


class DuckDuckGoSearchTool:
    """Tool for web and news search using DuckDuckGo.

    Free, no API key required. Implements rate limiting
    to avoid being blocked.
    """

    def __init__(self, cache: MemoryCache | None = None) -> None:
        """Initialize DuckDuckGo search tool.

        Args:
            cache: Optional cache instance
        """
        self._cache = cache or get_cache()
        self._ddgs = DDGS()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def search(
        self,
        query: str,
        max_results: int = 10,
        region: str = "wt-wt",
    ) -> list[SearchResult]:
        """Perform a web search.

        Args:
            query: Search query
            max_results: Maximum number of results (1-25)
            region: Region code (wt-wt for worldwide)

        Returns:
            List of SearchResult objects
        """
        cache_key = f"ddg:search:{query}:{max_results}"

        # Check cache
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug("ddg_search_cached", query=query)
            return [SearchResult(**r) for r in cached]

        # Rate limit
        search_limiter.acquire_sync("web")

        try:
            results = []
            raw_results = self._ddgs.text(
                query,
                max_results=max_results,
                region=region,
            )

            for r in raw_results:
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", r.get("link", "")),
                        snippet=r.get("body", r.get("snippet", "")),
                        source=r.get("source"),
                        published=r.get("published"),
                    )
                )

            # Cache results (15 min TTL for search)
            self._cache.set(cache_key, [r.to_dict() for r in results], ttl=900)
            logger.info("ddg_search_completed", query=query, results=len(results))

            return results

        except Exception as e:
            logger.error("ddg_search_error", query=query, error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def search_news(
        self,
        query: str,
        max_results: int = 10,
        timelimit: str | None = "w",  # d=day, w=week, m=month
    ) -> list[NewsResult]:
        """Search for news articles.

        Args:
            query: Search query
            max_results: Maximum number of results
            timelimit: Time filter (d=day, w=week, m=month, None=all)

        Returns:
            List of NewsResult objects
        """
        cache_key = f"ddg:news:{query}:{max_results}:{timelimit}"

        # Check cache
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug("ddg_news_cached", query=query)
            return [NewsResult(**r) for r in cached]

        # Rate limit
        search_limiter.acquire_sync("news")

        try:
            results = []
            raw_results = self._ddgs.news(
                query,
                max_results=max_results,
                timelimit=timelimit,
            )

            for r in raw_results:
                results.append(
                    NewsResult(
                        title=r.get("title", ""),
                        url=r.get("url", r.get("link", "")),
                        snippet=r.get("body", r.get("excerpt", "")),
                        source=r.get("source", ""),
                        date=r.get("date", ""),
                        image=r.get("image"),
                    )
                )

            # Cache results (10 min TTL for news)
            self._cache.set(cache_key, [r.to_dict() for r in results], ttl=600)
            logger.info("ddg_news_completed", query=query, results=len(results))

            return results

        except Exception as e:
            logger.error("ddg_news_error", query=query, error=str(e))
            raise

    def search_stock_news(self, ticker: str, company_name: str | None = None) -> list[NewsResult]:
        """Search for news about a specific stock.

        Args:
            ticker: Stock ticker symbol
            company_name: Company name (optional, enhances search)

        Returns:
            List of NewsResult objects
        """
        query = f"{ticker} stock"
        if company_name:
            query = f"{company_name} {ticker} stock news"

        return self.search_news(query, max_results=10, timelimit="w")

    def search_financial_topic(
        self,
        topic: str,
        company: str | None = None,
    ) -> list[SearchResult]:
        """Search for information about a financial topic.

        Args:
            topic: Financial topic (e.g., "China supply chain risks")
            company: Company context (optional)

        Returns:
            List of SearchResult objects
        """
        query = topic
        if company:
            query = f"{company} {topic}"

        return self.search(query, max_results=10)

"""Earnings call transcript fetcher using free sources."""

import re
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class EarningsCall:
    """Earnings call transcript data."""

    ticker: str
    quarter: str
    year: int
    date: str
    transcript: str
    participants: list[str]
    source: str


class EarningsCallTool:
    """Fetch earnings call transcripts from free sources.

    Sources (in priority order):
    1. Seeking Alpha (public transcripts via search)
    2. Motley Fool (free transcripts)
    3. DuckDuckGo fallback for summaries
    """

    def __init__(self) -> None:
        """Initialize earnings call tool."""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )

    async def get_latest_transcript(self, ticker: str) -> EarningsCall | None:
        """Get the most recent earnings call transcript.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            EarningsCall object or None if not found.
        """
        ticker = ticker.upper()

        # Try multiple sources
        transcript = await self._fetch_from_motley_fool(ticker)
        if transcript:
            return transcript

        # Fallback to search-based extraction
        transcript = await self._fetch_from_search(ticker)
        if transcript:
            return transcript

        logger.warning("earnings_call_not_found", ticker=ticker)
        return None

    async def _fetch_from_motley_fool(self, ticker: str) -> EarningsCall | None:
        """Fetch transcript from Motley Fool (free source)."""
        try:
            # Motley Fool has free transcripts
            url = f"https://www.fool.com/earnings-call-transcripts/?q={ticker}"
            response = await self.client.get(url)

            if response.status_code != 200:
                return None

            # Parse HTML for transcript links (simplified)
            html = response.text

            # Look for transcript content patterns
            # This is a simplified extraction - real implementation would use BeautifulSoup
            transcript_match = re.search(
                r'class="article-content"[^>]*>(.*?)</div>',
                html,
                re.DOTALL | re.IGNORECASE,
            )

            if not transcript_match:
                return None

            content = transcript_match.group(1)
            # Clean HTML tags
            content = re.sub(r"<[^>]+>", " ", content)
            content = re.sub(r"\s+", " ", content).strip()

            if len(content) < 500:  # Too short to be a real transcript
                return None

            # Extract quarter/year from content
            quarter_match = re.search(r"Q([1-4])\s*(?:FY\s*)?(\d{4})", content)
            quarter = f"Q{quarter_match.group(1)}" if quarter_match else "Unknown"
            year = int(quarter_match.group(2)) if quarter_match else datetime.now().year

            return EarningsCall(
                ticker=ticker,
                quarter=quarter,
                year=year,
                date=datetime.now().isoformat(),
                transcript=content[:50000],  # Limit size
                participants=self._extract_participants(content),
                source="motley_fool",
            )

        except Exception as e:
            logger.debug("motley_fool_fetch_failed", ticker=ticker, error=str(e))
            return None

    async def _fetch_from_search(self, ticker: str) -> EarningsCall | None:
        """Fallback: Search for earnings call info via DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS

            ddgs = DDGS()
            query = f"{ticker} earnings call transcript Q4 2024 OR Q3 2024"

            results = list(ddgs.text(query, max_results=5))

            if not results:
                return None

            # Combine search results as summary
            combined = "\n\n".join(
                f"**{r.get('title', 'No title')}**\n{r.get('body', '')}" for r in results
            )

            # Try to extract quarter info
            quarter_match = re.search(r"Q([1-4])\s*(?:FY\s*)?(\d{4})", combined)
            quarter = f"Q{quarter_match.group(1)}" if quarter_match else "Latest"
            year = int(quarter_match.group(2)) if quarter_match else datetime.now().year

            return EarningsCall(
                ticker=ticker,
                quarter=quarter,
                year=year,
                date=datetime.now().isoformat(),
                transcript=combined,
                participants=[],
                source="search_aggregation",
            )

        except Exception as e:
            logger.debug("search_fetch_failed", ticker=ticker, error=str(e))
            return None

    def _extract_participants(self, text: str) -> list[str]:
        """Extract participant names from transcript."""
        # Common patterns: "John Smith - CEO", "Jane Doe, CFO"
        patterns = [
            r"([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[-–]\s*(CEO|CFO|COO|CTO|President|VP)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+),\s*(CEO|CFO|COO|CTO|President|VP)",
        ]

        participants = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for name, title in matches:
                participants.add(f"{name} ({title})")

        return list(participants)[:10]  # Limit to 10

    async def search_historical(self, ticker: str, quarters: int = 4) -> list[EarningsCall]:
        """Search for historical earnings calls.

        Args:
            ticker: Stock ticker symbol.
            quarters: Number of quarters to look back.

        Returns:
            List of EarningsCall objects.
        """
        # For free tier, we can only reliably get the latest
        latest = await self.get_latest_transcript(ticker)
        return [latest] if latest else []

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


async def get_earnings_call(ticker: str) -> EarningsCall | None:
    """Convenience function to get latest earnings call.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        EarningsCall or None.
    """
    tool = EarningsCallTool()
    try:
        return await tool.get_latest_transcript(ticker)
    finally:
        await tool.close()

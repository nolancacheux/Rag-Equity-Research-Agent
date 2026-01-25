"""HTTP client to communicate with the Equity Research API."""

import httpx
from pydantic import BaseModel

from src.config.settings import get_settings


class QuoteResponse(BaseModel):
    """Stock quote response."""

    ticker: str
    price: float | None = None
    change_percent: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    volume: int | None = None
    error: str | None = None


class CompareResponse(BaseModel):
    """Comparison response."""

    tickers: list[str]
    data: list[dict] | None = None
    error: str | None = None


class AnalyzeResponse(BaseModel):
    """Analysis response."""

    query: str
    report: str | None = None
    sources: list[str] | None = None
    error: str | None = None


class APIClient:
    """Client to interact with the Equity Research FastAPI backend."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize the API client.

        Args:
            base_url: API base URL. Defaults to settings or localhost.
        """
        settings = get_settings()
        self.base_url = base_url or settings.api_base_url
        self.client = httpx.AsyncClient(timeout=120.0)  # Long timeout for analysis

    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def get_quote(self, ticker: str) -> QuoteResponse:
        """Get a stock quote.

        Args:
            ticker: Stock ticker symbol (e.g., NVDA).

        Returns:
            QuoteResponse with stock data or error.
        """
        try:
            response = await self.client.get(f"{self.base_url}/quote/{ticker.upper()}")
            if response.status_code == 200:
                json_data = response.json()
                # API returns {"success": true, "data": {...}, "error": null}
                if json_data.get("success") and json_data.get("data"):
                    data = json_data["data"]
                    return QuoteResponse(
                        ticker=data.get("symbol", ticker.upper()),
                        price=data.get("price"),
                        change_percent=data.get("change_percent"),
                        market_cap=data.get("market_cap"),
                        pe_ratio=data.get("pe_ratio"),
                        volume=data.get("volume"),
                    )
                return QuoteResponse(
                    ticker=ticker.upper(),
                    error=json_data.get("error") or "Unknown error",
                )
            return QuoteResponse(ticker=ticker.upper(), error=f"API error: {response.status_code}")
        except httpx.RequestError as e:
            return QuoteResponse(ticker=ticker.upper(), error=f"Connection error: {e}")

    async def compare(self, tickers: list[str]) -> CompareResponse:
        """Compare multiple stocks.

        Args:
            tickers: List of ticker symbols.

        Returns:
            CompareResponse with comparison data or error.
        """
        try:
            tickers_str = ",".join(t.upper() for t in tickers)
            response = await self.client.get(f"{self.base_url}/compare/{tickers_str}")
            if response.status_code == 200:
                data = response.json()
                return CompareResponse(tickers=tickers, data=data.get("comparisons", []))
            return CompareResponse(tickers=tickers, error=f"API error: {response.status_code}")
        except httpx.RequestError as e:
            return CompareResponse(tickers=tickers, error=f"Connection error: {e}")

    async def analyze(self, query: str, tickers: list[str] | None = None) -> AnalyzeResponse:
        """Run a full research analysis.

        Args:
            query: Natural language query.
            tickers: Optional list of tickers to focus on.

        Returns:
            AnalyzeResponse with report or error.
        """
        try:
            payload = {"query": query}
            if tickers:
                payload["tickers"] = tickers  # type: ignore[assignment]

            response = await self.client.post(
                f"{self.base_url}/analyze",
                json=payload,
            )
            if response.status_code == 200:
                data = response.json()
                return AnalyzeResponse(
                    query=query,
                    report=data.get("report"),
                    sources=data.get("sources", []),
                )
            return AnalyzeResponse(query=query, error=f"API error: {response.status_code}")
        except httpx.RequestError as e:
            return AnalyzeResponse(query=query, error=f"Connection error: {e}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

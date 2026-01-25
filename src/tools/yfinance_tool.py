"""Yahoo Finance tool for real-time market data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings
from src.utils.cache import RedisCache, get_cache
from src.utils.rate_limiter import yfinance_limiter

logger = structlog.get_logger()


@dataclass
class StockQuote:
    """Real-time stock quote data."""

    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float | None
    pe_ratio: float | None
    forward_pe: float | None
    dividend_yield: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None
    market_state: str
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "change": self.change,
            "change_percent": self.change_percent,
            "volume": self.volume,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "forward_pe": self.forward_pe,
            "dividend_yield": self.dividend_yield,
            "fifty_two_week_high": self.fifty_two_week_high,
            "fifty_two_week_low": self.fifty_two_week_low,
            "market_state": self.market_state,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FinancialMetrics:
    """Key financial metrics from statements."""

    symbol: str
    revenue: float | None
    net_income: float | None
    total_assets: float | None
    total_debt: float | None
    free_cash_flow: float | None
    operating_margin: float | None
    profit_margin: float | None
    return_on_equity: float | None
    debt_to_equity: float | None
    current_ratio: float | None
    fiscal_year_end: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "revenue": self.revenue,
            "net_income": self.net_income,
            "total_assets": self.total_assets,
            "total_debt": self.total_debt,
            "free_cash_flow": self.free_cash_flow,
            "operating_margin": self.operating_margin,
            "profit_margin": self.profit_margin,
            "return_on_equity": self.return_on_equity,
            "debt_to_equity": self.debt_to_equity,
            "current_ratio": self.current_ratio,
            "fiscal_year_end": self.fiscal_year_end,
        }


class YFinanceTool:
    """Tool for fetching real-time market data from Yahoo Finance.

    Implements caching and rate limiting to avoid API blocks.
    Handles NaN values and API errors gracefully.
    """

    def __init__(self, cache: RedisCache | None = None) -> None:
        """Initialize YFinance tool.

        Args:
            cache: Optional Redis cache instance
        """
        self._cache = cache or get_cache()
        self._settings = get_settings()

    def _safe_float(self, value: Any) -> float | None:
        """Safely convert value to float, handling NaN."""
        if value is None:
            return None
        try:
            import math

            f = float(value)
            return None if math.isnan(f) else f
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int."""
        if value is None:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def get_quote(self, symbol: str) -> StockQuote | None:
        """Get real-time stock quote.

        Args:
            symbol: Stock ticker symbol (e.g., "NVDA", "AAPL")

        Returns:
            StockQuote object or None if failed
        """
        cache_key = f"yf:quote:{symbol.upper()}"

        # Check cache first (outside retry logic)
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug("yfinance_quote_cached", symbol=symbol)
            return StockQuote(
                **{**cached, "timestamp": datetime.fromisoformat(cached["timestamp"])}
            )

        # Fetch with retry
        return self._fetch_quote_with_retry(symbol, cache_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _fetch_quote_with_retry(self, symbol: str, cache_key: str) -> StockQuote | None:
        """Fetch quote from yfinance with retry logic."""

        # Rate limit
        yfinance_limiter.acquire_sync("quote")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or "symbol" not in info:
                logger.warning("yfinance_no_data", symbol=symbol)
                return None

            quote = StockQuote(
                symbol=info.get("symbol", symbol.upper()),
                name=info.get("longName", info.get("shortName", symbol)),
                price=self._safe_float(info.get("currentPrice", info.get("regularMarketPrice")))
                or 0.0,
                change=self._safe_float(info.get("regularMarketChange")) or 0.0,
                change_percent=self._safe_float(info.get("regularMarketChangePercent")) or 0.0,
                volume=self._safe_int(info.get("regularMarketVolume")),
                market_cap=self._safe_float(info.get("marketCap")),
                pe_ratio=self._safe_float(info.get("trailingPE")),
                forward_pe=self._safe_float(info.get("forwardPE")),
                dividend_yield=self._safe_float(info.get("dividendYield")),
                fifty_two_week_high=self._safe_float(info.get("fiftyTwoWeekHigh")),
                fifty_two_week_low=self._safe_float(info.get("fiftyTwoWeekLow")),
                market_state=info.get("marketState", "UNKNOWN"),
                timestamp=datetime.now(),
            )

            # Cache the result
            self._cache.set(cache_key, quote.to_dict(), ttl=self._settings.yfinance_cache_ttl)
            logger.info("yfinance_quote_fetched", symbol=symbol, price=quote.price)

            return quote

        except Exception as e:
            logger.error("yfinance_quote_error", symbol=symbol, error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get_financials(self, symbol: str) -> FinancialMetrics | None:
        """Get key financial metrics.

        Args:
            symbol: Stock ticker symbol

        Returns:
            FinancialMetrics object or None if failed
        """
        cache_key = f"yf:financials:{symbol.upper()}"

        # Check cache (longer TTL for financials as they change less frequently)
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug("yfinance_financials_cached", symbol=symbol)
            return FinancialMetrics(**cached)

        # Rate limit
        yfinance_limiter.acquire_sync("financials")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                logger.warning("yfinance_no_financials", symbol=symbol)
                return None

            metrics = FinancialMetrics(
                symbol=symbol.upper(),
                revenue=self._safe_float(info.get("totalRevenue")),
                net_income=self._safe_float(info.get("netIncomeToCommon")),
                total_assets=self._safe_float(info.get("totalAssets")),
                total_debt=self._safe_float(info.get("totalDebt")),
                free_cash_flow=self._safe_float(info.get("freeCashflow")),
                operating_margin=self._safe_float(info.get("operatingMargins")),
                profit_margin=self._safe_float(info.get("profitMargins")),
                return_on_equity=self._safe_float(info.get("returnOnEquity")),
                debt_to_equity=self._safe_float(info.get("debtToEquity")),
                current_ratio=self._safe_float(info.get("currentRatio")),
                fiscal_year_end=info.get("lastFiscalYearEnd"),
            )

            # Cache with longer TTL (1 hour)
            self._cache.set(cache_key, metrics.to_dict(), ttl=3600)
            logger.info("yfinance_financials_fetched", symbol=symbol)

            return metrics

        except Exception as e:
            logger.error("yfinance_financials_error", symbol=symbol, error=str(e))
            raise

    def compare_pe_ratios(self, symbols: list[str]) -> dict[str, float | None]:
        """Compare P/E ratios across multiple stocks.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dictionary of symbol -> P/E ratio
        """
        results = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            results[symbol] = quote.pe_ratio if quote else None

        logger.info("yfinance_pe_comparison", symbols=symbols, results=results)
        return results

"""Automatic peer comparison service."""

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


# Industry peer mappings (manually curated for accuracy)
PEER_GROUPS = {
    # Semiconductors
    "NVDA": ["AMD", "INTC", "QCOM", "AVGO", "TSM"],
    "AMD": ["NVDA", "INTC", "QCOM", "AVGO", "TSM"],
    "INTC": ["NVDA", "AMD", "QCOM", "AVGO", "TSM"],
    "TSM": ["NVDA", "AMD", "INTC", "ASML", "AVGO"],
    # Big Tech
    "AAPL": ["MSFT", "GOOGL", "AMZN", "META"],
    "MSFT": ["AAPL", "GOOGL", "AMZN", "META", "ORCL"],
    "GOOGL": ["AAPL", "MSFT", "AMZN", "META"],
    "AMZN": ["MSFT", "GOOGL", "AAPL", "META", "WMT"],
    "META": ["GOOGL", "SNAP", "PINS", "AAPL", "MSFT"],
    # EV & Auto
    "TSLA": ["RIVN", "LCID", "F", "GM", "NIO"],
    "RIVN": ["TSLA", "LCID", "F", "GM"],
    "F": ["GM", "TSLA", "TM", "STLA"],
    "GM": ["F", "TSLA", "TM", "STLA"],
    # Financials
    "JPM": ["BAC", "WFC", "C", "GS", "MS"],
    "BAC": ["JPM", "WFC", "C", "GS"],
    "GS": ["MS", "JPM", "BAC", "C"],
    # Streaming & Entertainment
    "NFLX": ["DIS", "WBD", "PARA", "CMCSA"],
    "DIS": ["NFLX", "WBD", "PARA", "CMCSA"],
    # E-commerce
    "SHOP": ["WIX", "BIGC", "AMZN", "EBAY"],
    "EBAY": ["AMZN", "ETSY", "SHOP"],
    # Cloud
    "CRM": ["NOW", "WDAY", "ORCL", "SAP"],
    "SNOW": ["DDOG", "MDB", "CRM", "PLTR"],
    # Pharma
    "PFE": ["JNJ", "MRK", "ABBV", "LLY"],
    "JNJ": ["PFE", "MRK", "ABBV", "UNH"],
    # Airlines
    "DAL": ["UAL", "AAL", "LUV", "JBLU"],
    "UAL": ["DAL", "AAL", "LUV"],
    # Retail
    "WMT": ["TGT", "COST", "AMZN", "HD"],
    "TGT": ["WMT", "COST", "HD", "LOW"],
    "COST": ["WMT", "TGT", "BJ"],
}


@dataclass
class PeerMetrics:
    """Metrics for a single peer."""

    ticker: str
    price: float | None
    pe_ratio: float | None
    market_cap: float | None
    revenue_growth: float | None
    profit_margin: float | None


@dataclass
class PeerComparison:
    """Complete peer comparison result."""

    ticker: str
    industry: str
    peers: list[PeerMetrics]
    ticker_metrics: PeerMetrics
    pe_percentile: float | None  # Where ticker ranks in PE (0-100)
    summary: str


class PeerComparisonService:
    """Service for automatic peer comparison."""

    def __init__(self) -> None:
        """Initialize peer comparison service."""
        self._yfinance_tool = None

    def _get_yfinance_tool(self):
        """Lazy load yfinance tool."""
        if self._yfinance_tool is None:
            from src.tools.yfinance_tool import YFinanceTool

            self._yfinance_tool = YFinanceTool()
        return self._yfinance_tool

    def get_peers(self, ticker: str) -> list[str]:
        """Get peer tickers for a given stock.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            List of peer ticker symbols.
        """
        ticker = ticker.upper()
        return PEER_GROUPS.get(ticker, [])

    async def compare_with_peers(self, ticker: str) -> PeerComparison:
        """Compare a stock with its peers.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            PeerComparison with metrics and analysis.
        """
        ticker = ticker.upper()
        tool = self._get_yfinance_tool()

        # Get peers
        peer_tickers = self.get_peers(ticker)
        if not peer_tickers:
            # Try to find similar stocks by sector
            peer_tickers = await self._find_peers_by_sector(ticker)

        # Fetch metrics for main ticker
        ticker_quote = tool.get_quote(ticker)
        ticker_metrics = PeerMetrics(
            ticker=ticker,
            price=ticker_quote.price if ticker_quote else None,
            pe_ratio=ticker_quote.pe_ratio if ticker_quote else None,
            market_cap=ticker_quote.market_cap if ticker_quote else None,
            revenue_growth=None,  # Would need additional API call
            profit_margin=None,
        )

        # Fetch metrics for peers
        peer_metrics = []
        pe_values = []

        if ticker_metrics.pe_ratio:
            pe_values.append(ticker_metrics.pe_ratio)

        for peer in peer_tickers[:5]:  # Limit to 5 peers
            try:
                quote = tool.get_quote(peer)
                if quote:
                    metrics = PeerMetrics(
                        ticker=peer,
                        price=quote.price,
                        pe_ratio=quote.pe_ratio,
                        market_cap=quote.market_cap,
                        revenue_growth=None,
                        profit_margin=None,
                    )
                    peer_metrics.append(metrics)
                    if quote.pe_ratio:
                        pe_values.append(quote.pe_ratio)
            except Exception as e:
                logger.debug("peer_fetch_failed", peer=peer, error=str(e))

        # Calculate PE percentile
        pe_percentile = None
        if ticker_metrics.pe_ratio and len(pe_values) > 1:
            sorted_pes = sorted(pe_values)
            rank = sorted_pes.index(ticker_metrics.pe_ratio)
            pe_percentile = (rank / (len(sorted_pes) - 1)) * 100

        # Generate summary
        summary = self._generate_summary(ticker, ticker_metrics, peer_metrics, pe_percentile)

        # Detect industry from peers
        industry = self._detect_industry(ticker)

        return PeerComparison(
            ticker=ticker,
            industry=industry,
            peers=peer_metrics,
            ticker_metrics=ticker_metrics,
            pe_percentile=pe_percentile,
            summary=summary,
        )

    async def _find_peers_by_sector(self, ticker: str) -> list[str]:
        """Find peers by sector if not in predefined list."""
        # For now, return empty list
        # Could use yfinance sector info in the future
        return []

    def _detect_industry(self, ticker: str) -> str:
        """Detect industry from peer groupings."""
        ticker = ticker.upper()

        # Check which group contains this ticker
        for group_ticker, peers in PEER_GROUPS.items():
            if ticker == group_ticker or ticker in peers:
                # Determine industry based on known tickers
                if ticker in ["NVDA", "AMD", "INTC", "TSM", "QCOM", "AVGO", "ASML"]:
                    return "Semiconductors"
                elif ticker in ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]:
                    return "Big Tech"
                elif ticker in ["TSLA", "RIVN", "LCID", "F", "GM", "NIO"]:
                    return "Automotive"
                elif ticker in ["JPM", "BAC", "WFC", "C", "GS", "MS"]:
                    return "Financials"
                elif ticker in ["NFLX", "DIS", "WBD", "PARA"]:
                    return "Entertainment"
                elif ticker in ["PFE", "JNJ", "MRK", "ABBV", "LLY"]:
                    return "Pharmaceuticals"
                elif ticker in ["WMT", "TGT", "COST"]:
                    return "Retail"

        return "Unknown"

    def _generate_summary(
        self,
        ticker: str,
        ticker_metrics: PeerMetrics,
        peer_metrics: list[PeerMetrics],
        pe_percentile: float | None,
    ) -> str:
        """Generate human-readable comparison summary."""
        lines = [f"**{ticker} Peer Comparison**\n"]

        if ticker_metrics.pe_ratio:
            if pe_percentile is not None:
                if pe_percentile > 75:
                    lines.append(
                        f"P/E of {ticker_metrics.pe_ratio:.1f} is HIGH vs peers (top {100 - pe_percentile:.0f}%)"
                    )
                elif pe_percentile < 25:
                    lines.append(
                        f"P/E of {ticker_metrics.pe_ratio:.1f} is LOW vs peers (bottom {pe_percentile:.0f}%)"
                    )
                else:
                    lines.append(f"P/E of {ticker_metrics.pe_ratio:.1f} is AVERAGE vs peers")

        if peer_metrics:
            avg_pe = sum(p.pe_ratio for p in peer_metrics if p.pe_ratio) / max(
                sum(1 for p in peer_metrics if p.pe_ratio), 1
            )
            if avg_pe > 0:
                lines.append(f"Peer average P/E: {avg_pe:.1f}")

            # Market cap comparison
            if ticker_metrics.market_cap:
                larger = sum(
                    1
                    for p in peer_metrics
                    if p.market_cap and p.market_cap > ticker_metrics.market_cap
                )
                total = sum(1 for p in peer_metrics if p.market_cap)
                if total > 0:
                    lines.append(f"Market cap rank: #{larger + 1} of {total + 1} peers")

        return "\n".join(lines)


# Singleton instance
_peer_service: PeerComparisonService | None = None


def get_peer_service() -> PeerComparisonService:
    """Get singleton peer comparison service."""
    global _peer_service
    if _peer_service is None:
        _peer_service = PeerComparisonService()
    return _peer_service

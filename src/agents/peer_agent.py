"""Peer Comparison Agent for competitive analysis."""

from dataclasses import dataclass
from typing import Any

import structlog

from src.services.peer_comparison import PeerComparisonService

logger = structlog.get_logger()


@dataclass
class PeerAnalysis:
    """Result from peer comparison analysis."""

    ticker: str
    sector: str | None
    industry: str | None
    peers: list[str]
    metrics_comparison: dict[str, dict]
    ranking: dict[str, int]  # metric -> rank among peers
    strengths: list[str]
    weaknesses: list[str]
    summary: str
    errors: list[str]


class PeerComparisonAgent:
    """Agent for comparing a stock with its peers.

    Responsibilities:
    - Identify peer companies (same sector/industry)
    - Compare key financial metrics
    - Rank performance vs peers
    """

    def __init__(self) -> None:
        """Initialize peer comparison agent."""
        self._service = PeerComparisonService()

    async def compare_peers(self, ticker: str, num_peers: int = 5) -> PeerAnalysis:
        """Compare a ticker with its peers.

        Args:
            ticker: Stock ticker symbol
            num_peers: Number of peers to compare (default 5)

        Returns:
            PeerAnalysis with comparison results
        """
        ticker = ticker.upper()
        errors = []

        try:
            result = await self._service.compare_with_peers(ticker)
        except Exception as e:
            logger.error("peer_comparison_failed", ticker=ticker, error=str(e))
            return PeerAnalysis(
                ticker=ticker,
                sector=None,
                industry=None,
                peers=[],
                metrics_comparison={},
                ranking={},
                strengths=[],
                weaknesses=[],
                summary=f"Could not compare peers for {ticker}: {e}",
                errors=[str(e)],
            )

        if not result or not result.peers:
            return PeerAnalysis(
                ticker=ticker,
                sector=None,
                industry=None,
                peers=[],
                metrics_comparison={},
                ranking={},
                strengths=[],
                weaknesses=[],
                summary=f"No peers found for {ticker}",
                errors=["No peers found"],
            )

        # Build peer list and metrics comparison
        peer_tickers = [p.ticker for p in result.peers]

        # Build metrics comparison dict
        metrics_comparison = {
            "PE Ratio": {},
            "Market Cap": {},
            "Price": {},
        }

        # Add ticker metrics
        if result.ticker_metrics:
            tm = result.ticker_metrics
            metrics_comparison["PE Ratio"][ticker] = tm.pe_ratio
            metrics_comparison["Market Cap"][ticker] = tm.market_cap
            metrics_comparison["Price"][ticker] = tm.price

        # Add peer metrics
        for peer in result.peers:
            metrics_comparison["PE Ratio"][peer.ticker] = peer.pe_ratio
            metrics_comparison["Market Cap"][peer.ticker] = peer.market_cap
            metrics_comparison["Price"][peer.ticker] = peer.price

        # Calculate rankings
        ranking = {}
        for metric_name, values in metrics_comparison.items():
            valid_values = [(t, v) for t, v in values.items() if v is not None]
            if valid_values:
                # Sort: lower PE is better, higher market cap is better
                reverse = metric_name != "PE Ratio"
                sorted_values = sorted(valid_values, key=lambda x: x[1], reverse=reverse)
                for rank, (t, _) in enumerate(sorted_values, 1):
                    if t == ticker:
                        ranking[metric_name] = rank
                        break

        # Analyze strengths and weaknesses based on ranking
        strengths = []
        weaknesses = []
        num_companies = len(peer_tickers) + 1

        for metric, rank in ranking.items():
            if rank == 1:
                strengths.append(f"Best {metric} among peers")
            elif rank <= 2:
                strengths.append(f"Top 2 in {metric}")
            elif rank >= num_companies:
                weaknesses.append(f"Lowest {metric} among peers")
            elif rank >= num_companies - 1:
                weaknesses.append(f"Below average {metric}")

        # Use result summary or generate one
        summary = (
            result.summary
            if result.summary
            else self._generate_summary(ticker, result, strengths, weaknesses)
        )

        return PeerAnalysis(
            ticker=ticker,
            sector=result.industry,  # Use industry as sector
            industry=result.industry,
            peers=peer_tickers,
            metrics_comparison=metrics_comparison,
            ranking=ranking,
            strengths=strengths[:5],
            weaknesses=weaknesses[:5],
            summary=summary,
            errors=errors,
        )

    def _generate_summary(
        self,
        ticker: str,
        result: Any,
        strengths: list[str],
        weaknesses: list[str],
    ) -> str:
        """Generate comparison summary."""
        peer_tickers = [p.ticker for p in result.peers] if result.peers else []

        lines = [f"## Peer Comparison: {ticker}"]
        lines.append(f"**Industry**: {result.industry or 'N/A'}")
        lines.append(f"**Peers**: {', '.join(peer_tickers)}")
        lines.append("")

        # Key metrics
        if result.ticker_metrics:
            lines.append("### Key Metrics")
            tm = result.ticker_metrics
            if tm.pe_ratio:
                lines.append(f"- **P/E Ratio**: {tm.pe_ratio:.2f}")
            if tm.market_cap:
                lines.append(f"- **Market Cap**: ${tm.market_cap / 1e9:.1f}B")
            if tm.price:
                lines.append(f"- **Price**: ${tm.price:.2f}")
            lines.append("")

        if result.pe_percentile is not None:
            lines.append(f"**PE Percentile**: {result.pe_percentile:.0f}% (vs peers)")
            lines.append("")

        if strengths:
            lines.append("### Strengths")
            for s in strengths[:3]:
                lines.append(f"- {s}")
            lines.append("")

        if weaknesses:
            lines.append("### Weaknesses")
            for w in weaknesses[:3]:
                lines.append(f"- {w}")

        return "\n".join(lines)


async def run_peer_agent_node(state: dict) -> dict:
    """LangGraph node function for peer comparison agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with peer analysis
    """
    tickers = state.get("tickers", [])

    if not tickers:
        return {
            "peer_analysis": None,
            "errors": state.get("errors", []) + ["No tickers provided for peer comparison"],
        }

    agent = PeerComparisonAgent()
    all_results = []
    all_errors = []

    # Only analyze first ticker to avoid too many API calls
    ticker = tickers[0]
    result = await agent.compare_peers(ticker)
    all_results.append(
        {
            "ticker": result.ticker,
            "sector": result.sector,
            "industry": result.industry,
            "peers": result.peers,
            "metrics": result.metrics_comparison,
            "ranking": result.ranking,
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "summary": result.summary,
        }
    )
    all_errors.extend(result.errors)

    return {
        "peer_analysis": all_results,
        "errors": state.get("errors", []) + all_errors,
    }

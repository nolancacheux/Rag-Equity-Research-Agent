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
            result = await self._service.compare(ticker, num_peers=num_peers)
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

        # Analyze strengths and weaknesses based on ranking
        strengths = []
        weaknesses = []
        
        for metric, rank in result.ranking.items():
            if rank == 1:
                strengths.append(f"Best {metric} among peers")
            elif rank <= 2:
                strengths.append(f"Top 2 in {metric}")
            elif rank >= len(result.peers):
                weaknesses.append(f"Lowest {metric} among peers")
            elif rank >= len(result.peers) - 1:
                weaknesses.append(f"Below average {metric}")

        summary = self._generate_summary(ticker, result, strengths, weaknesses)

        return PeerAnalysis(
            ticker=ticker,
            sector=result.sector,
            industry=result.industry,
            peers=result.peers,
            metrics_comparison=result.metrics,
            ranking=result.ranking,
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
        lines = [f"## Peer Comparison: {ticker}"]
        lines.append(f"**Sector**: {result.sector or 'N/A'}")
        lines.append(f"**Industry**: {result.industry or 'N/A'}")
        lines.append(f"**Peers**: {', '.join(result.peers)}")
        lines.append("")
        
        # Key metrics table
        lines.append("### Key Metrics")
        lines.append("| Metric | Value | Rank |")
        lines.append("|--------|-------|------|")
        
        for metric, values in result.metrics.items():
            ticker_value = values.get(ticker, "N/A")
            rank = result.ranking.get(metric, "-")
            lines.append(f"| {metric} | {ticker_value} | #{rank} |")
        
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
    all_results.append({
        "ticker": result.ticker,
        "sector": result.sector,
        "industry": result.industry,
        "peers": result.peers,
        "metrics": result.metrics_comparison,
        "ranking": result.ranking,
        "strengths": result.strengths,
        "weaknesses": result.weaknesses,
        "summary": result.summary,
    })
    all_errors.extend(result.errors)

    return {
        "peer_analysis": all_results,
        "errors": state.get("errors", []) + all_errors,
    }

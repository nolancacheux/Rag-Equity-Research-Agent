"""Earnings Call Agent for transcript analysis."""

from dataclasses import dataclass
from typing import Any

import structlog

from src.tools.earnings_call_tool import EarningsCallTool

logger = structlog.get_logger()


@dataclass
class EarningsAnalysis:
    """Result from earnings call analysis."""

    ticker: str
    quarter: str | None
    year: int | None
    key_points: list[str]
    guidance: str | None
    sentiment: str  # positive, negative, neutral
    summary: str
    errors: list[str]


class EarningsAgent:
    """Agent for fetching and analyzing earnings call transcripts.

    Responsibilities:
    - Fetch latest earnings call transcripts
    - Extract key points and guidance
    - Analyze management tone/sentiment
    """

    def __init__(self) -> None:
        """Initialize earnings agent."""
        self._tool = EarningsCallTool()

    async def analyze_earnings(self, ticker: str) -> EarningsAnalysis:
        """Analyze the latest earnings call for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            EarningsAnalysis with key insights
        """
        ticker = ticker.upper()
        errors = []

        try:
            transcript = await self._tool.get_latest_transcript(ticker)
        except Exception as e:
            logger.error("earnings_fetch_failed", ticker=ticker, error=str(e))
            return EarningsAnalysis(
                ticker=ticker,
                quarter=None,
                year=None,
                key_points=[],
                guidance=None,
                sentiment="neutral",
                summary=f"Could not fetch earnings call for {ticker}: {e}",
                errors=[str(e)],
            )

        if not transcript:
            return EarningsAnalysis(
                ticker=ticker,
                quarter=None,
                year=None,
                key_points=[],
                guidance=None,
                sentiment="neutral",
                summary=f"No earnings call transcript found for {ticker}",
                errors=["Transcript not found"],
            )

        # Extract key points from transcript
        key_points = self._extract_key_points(transcript.transcript)
        guidance = self._extract_guidance(transcript.transcript)
        sentiment = self._analyze_sentiment(transcript.transcript)

        summary = self._generate_summary(ticker, transcript, key_points, guidance, sentiment)

        return EarningsAnalysis(
            ticker=ticker,
            quarter=transcript.quarter,
            year=transcript.year,
            key_points=key_points,
            guidance=guidance,
            sentiment=sentiment,
            summary=summary,
            errors=errors,
        )

    def _extract_key_points(self, transcript: str) -> list[str]:
        """Extract key points from transcript."""
        key_points = []
        
        # Look for common patterns
        patterns = [
            r"(?:revenue|sales)\s+(?:grew|increased|up)\s+(\d+%?[^.]*)",
            r"(?:earnings|EPS)\s+(?:of|at|was)\s+\$?([\d.]+[^.]*)",
            r"(?:guidance|outlook)[:\s]+([^.]+\.)",
            r"(?:we expect|we anticipate|we project)[^.]+\.",
            r"(?:margin|margins)\s+(?:expanded|improved|grew)[^.]+\.",
        ]
        
        import re
        for pattern in patterns:
            matches = re.findall(pattern, transcript.lower(), re.IGNORECASE)
            for match in matches[:2]:  # Limit per pattern
                if isinstance(match, str) and len(match) > 10:
                    key_points.append(match.strip().capitalize())
        
        return key_points[:5]  # Top 5 key points

    def _extract_guidance(self, transcript: str) -> str | None:
        """Extract forward guidance from transcript."""
        import re
        
        guidance_patterns = [
            r"(?:for (?:the )?(?:full )?year|FY\d+)[,\s]+we (?:expect|anticipate|project)[^.]+\.",
            r"(?:guidance|outlook)\s*(?:for|is)[^.]+\.",
            r"we (?:are raising|are maintaining|are lowering)[^.]+guidance[^.]+\.",
        ]
        
        for pattern in guidance_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None

    def _analyze_sentiment(self, transcript: str) -> str:
        """Analyze overall sentiment of the call."""
        positive_words = {
            "strong", "growth", "exceeded", "beat", "optimistic", "confident",
            "record", "momentum", "excited", "pleased", "outstanding",
        }
        negative_words = {
            "challenging", "headwinds", "decline", "missed", "weakness",
            "cautious", "uncertain", "concern", "pressure", "difficult",
        }
        
        transcript_lower = transcript.lower()
        positive_count = sum(1 for word in positive_words if word in transcript_lower)
        negative_count = sum(1 for word in negative_words if word in transcript_lower)
        
        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        return "neutral"

    def _generate_summary(
        self,
        ticker: str,
        transcript: Any,
        key_points: list[str],
        guidance: str | None,
        sentiment: str,
    ) -> str:
        """Generate analysis summary."""
        lines = [f"## Earnings Call Analysis: {ticker}"]
        lines.append(f"**Period**: {transcript.quarter} {transcript.year}")
        lines.append(f"**Date**: {transcript.date}")
        lines.append(f"**Sentiment**: {sentiment.capitalize()}")
        lines.append("")
        
        if key_points:
            lines.append("### Key Points")
            for point in key_points:
                lines.append(f"- {point}")
            lines.append("")
        
        if guidance:
            lines.append("### Forward Guidance")
            lines.append(guidance)
        
        return "\n".join(lines)


async def run_earnings_agent_node(state: dict) -> dict:
    """LangGraph node function for earnings agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with earnings analysis
    """
    tickers = state.get("tickers", [])

    if not tickers:
        return {
            "earnings_analysis": None,
            "errors": state.get("errors", []) + ["No tickers provided for earnings"],
        }

    agent = EarningsAgent()
    all_results = []
    all_errors = []

    for ticker in tickers:
        result = await agent.analyze_earnings(ticker)
        all_results.append({
            "ticker": result.ticker,
            "quarter": result.quarter,
            "year": result.year,
            "key_points": result.key_points,
            "guidance": result.guidance,
            "sentiment": result.sentiment,
            "summary": result.summary,
        })
        all_errors.extend(result.errors)

    return {
        "earnings_analysis": all_results,
        "errors": state.get("errors", []) + all_errors,
    }

"""Reddit Sentiment Agent for social sentiment analysis."""

from dataclasses import dataclass
from typing import Any

import structlog

from src.tools.reddit_sentiment_tool import RedditSentimentTool

logger = structlog.get_logger()


@dataclass
class SocialSentiment:
    """Result from social sentiment analysis."""

    ticker: str
    sentiment_score: float  # -1 (bearish) to 1 (bullish)
    sentiment_label: str  # bullish, bearish, neutral
    total_mentions: int
    bullish_ratio: float
    trending_topics: list[str]
    top_discussions: list[dict]
    summary: str
    errors: list[str]


class RedditSentimentAgent:
    """Agent for analyzing Reddit sentiment on stocks.

    Responsibilities:
    - Fetch posts from r/wallstreetbets, r/stocks, etc.
    - Analyze sentiment distribution
    - Identify trending topics and discussions
    """

    def __init__(self) -> None:
        """Initialize Reddit sentiment agent."""
        self._tool = RedditSentimentTool()

    async def analyze_sentiment(self, ticker: str) -> SocialSentiment:
        """Analyze Reddit sentiment for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            SocialSentiment with analysis results
        """
        ticker = ticker.upper()
        errors = []

        try:
            result = await self._tool.get_sentiment(ticker)
        except Exception as e:
            logger.error("reddit_fetch_failed", ticker=ticker, error=str(e))
            return SocialSentiment(
                ticker=ticker,
                sentiment_score=0.0,
                sentiment_label="neutral",
                total_mentions=0,
                bullish_ratio=0.5,
                trending_topics=[],
                top_discussions=[],
                summary=f"Could not fetch Reddit sentiment for {ticker}: {e}",
                errors=[str(e)],
            )

        if not result or result.total_posts == 0:
            return SocialSentiment(
                ticker=ticker,
                sentiment_score=0.0,
                sentiment_label="neutral",
                total_mentions=0,
                bullish_ratio=0.5,
                trending_topics=[],
                top_discussions=[],
                summary=f"No Reddit discussions found for {ticker}",
                errors=[],
            )

        # Calculate sentiment label
        if result.sentiment_score > 0.2:
            sentiment_label = "bullish"
        elif result.sentiment_score < -0.2:
            sentiment_label = "bearish"
        else:
            sentiment_label = "neutral"

        # Calculate bullish ratio
        total_sentiment = result.bullish_count + result.bearish_count
        bullish_ratio = result.bullish_count / total_sentiment if total_sentiment > 0 else 0.5

        # Format top discussions
        top_discussions = [
            {
                "title": post.title,
                "subreddit": post.subreddit,
                "score": post.score,
                "comments": post.num_comments,
                "sentiment": post.sentiment,
                "url": post.url,
            }
            for post in result.top_posts[:5]
        ]

        summary = self._generate_summary(
            ticker, result, sentiment_label, bullish_ratio, top_discussions
        )

        return SocialSentiment(
            ticker=ticker,
            sentiment_score=result.sentiment_score,
            sentiment_label=sentiment_label,
            total_mentions=result.total_posts,
            bullish_ratio=bullish_ratio,
            trending_topics=result.trending_keywords[:10],
            top_discussions=top_discussions,
            summary=summary,
            errors=errors,
        )

    def _generate_summary(
        self,
        ticker: str,
        result: Any,
        sentiment_label: str,
        bullish_ratio: float,
        top_discussions: list[dict],
    ) -> str:
        """Generate analysis summary."""
        emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(sentiment_label, "⚪")
        
        lines = [f"## Reddit Sentiment: {ticker} {emoji}"]
        lines.append(f"**Overall**: {sentiment_label.capitalize()} ({result.sentiment_score:+.2f})")
        lines.append(f"**Mentions**: {result.total_posts} posts")
        lines.append(f"**Bullish/Bearish**: {result.bullish_count}/{result.bearish_count}")
        lines.append(f"**Bullish Ratio**: {bullish_ratio:.0%}")
        lines.append("")
        
        if result.trending_keywords:
            lines.append("### Trending Topics")
            lines.append(", ".join(result.trending_keywords[:5]))
            lines.append("")
        
        if top_discussions:
            lines.append("### Top Discussions")
            for disc in top_discussions[:3]:
                lines.append(f"- [{disc['subreddit']}] {disc['title'][:60]}... ({disc['sentiment']})")
        
        return "\n".join(lines)


async def run_reddit_agent_node(state: dict) -> dict:
    """LangGraph node function for Reddit sentiment agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with Reddit sentiment analysis
    """
    tickers = state.get("tickers", [])

    if not tickers:
        return {
            "reddit_sentiment": None,
            "errors": state.get("errors", []) + ["No tickers provided for Reddit analysis"],
        }

    agent = RedditSentimentAgent()
    all_results = []
    all_errors = []

    for ticker in tickers:
        result = await agent.analyze_sentiment(ticker)
        all_results.append({
            "ticker": result.ticker,
            "sentiment_score": result.sentiment_score,
            "sentiment_label": result.sentiment_label,
            "total_mentions": result.total_mentions,
            "bullish_ratio": result.bullish_ratio,
            "trending_topics": result.trending_topics,
            "top_discussions": result.top_discussions,
            "summary": result.summary,
        })
        all_errors.extend(result.errors)

    return {
        "reddit_sentiment": all_results,
        "errors": state.get("errors", []) + all_errors,
    }

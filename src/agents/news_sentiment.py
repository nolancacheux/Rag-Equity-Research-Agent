"""News Sentiment Agent for real-time news analysis."""

from dataclasses import dataclass
from typing import Any

import structlog

from src.tools import DuckDuckGoSearchTool

logger = structlog.get_logger()


@dataclass
class NewsAnalysisResult:
    """Result from news analysis."""

    ticker: str
    company_name: str | None
    articles: list[dict[str, Any]]
    summary: str
    errors: list[str]


class NewsSentimentAgent:
    """Agent for gathering and analyzing news sentiment.

    Responsibilities:
    - Search for recent news about stocks
    - Aggregate news from multiple sources
    - Provide sentiment context
    """

    def __init__(self) -> None:
        """Initialize news sentiment agent."""
        self._search_tool = DuckDuckGoSearchTool()

    def analyze(
        self,
        ticker: str,
        company_name: str | None = None,
        max_articles: int = 10,
    ) -> NewsAnalysisResult:
        """Analyze news sentiment for a stock.

        Args:
            ticker: Stock ticker symbol
            company_name: Company name (optional)
            max_articles: Maximum articles to fetch

        Returns:
            NewsAnalysisResult with articles and summary
        """
        ticker = ticker.upper()
        errors = []

        # Search for news
        try:
            news = self._search_tool.search_stock_news(ticker, company_name)
            articles = [n.to_dict() for n in news[:max_articles]]
        except Exception as e:
            logger.error("news_search_failed", ticker=ticker, error=str(e))
            errors.append(f"News search failed: {str(e)}")
            articles = []

        # Generate summary
        summary = self._generate_summary(ticker, company_name, articles)

        logger.info("news_analyzed", ticker=ticker, articles=len(articles))

        return NewsAnalysisResult(
            ticker=ticker,
            company_name=company_name,
            articles=articles,
            summary=summary,
            errors=errors,
        )

    def _generate_summary(
        self,
        ticker: str,
        company_name: str | None,
        articles: list[dict[str, Any]],
    ) -> str:
        """Generate a summary of news articles."""
        display_name = company_name or ticker

        if not articles:
            return f"No recent news found for {display_name}."

        lines = [f"## Recent News: {display_name} ({ticker})\n"]
        lines.append(f"**{len(articles)} recent articles found**\n")

        for i, article in enumerate(articles, 1):
            title = article.get("title", "Untitled")
            source = article.get("source", "Unknown")
            date = article.get("date", "")
            snippet = article.get("snippet", "")
            url = article.get("url", "")

            lines.append(f"### {i}. {title}")
            lines.append(f"**Source**: {source} | **Date**: {date}")
            if snippet:
                lines.append(f"> {snippet[:300]}{'...' if len(snippet) > 300 else ''}")
            if url:
                lines.append(f"[Read more]({url})")
            lines.append("")

        return "\n".join(lines)

    def search_topic(
        self,
        topic: str,
        ticker: str | None = None,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for a specific financial topic.

        Args:
            topic: Topic to search (e.g., "China supply chain risks")
            ticker: Optional ticker for context
            max_results: Maximum results

        Returns:
            List of search results
        """
        try:
            results = self._search_tool.search_financial_topic(topic, ticker)
            return [r.to_dict() for r in results[:max_results]]
        except Exception as e:
            logger.error("topic_search_failed", topic=topic, error=str(e))
            return []


def run_news_sentiment_node(state: dict) -> dict:
    """LangGraph node function for news sentiment agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with news analysis
    """
    tickers = state.get("tickers", [])
    market_data = state.get("market_data", {})

    if not tickers:
        return {
            "news_analysis": None,
            "errors": state.get("errors", []) + ["No tickers provided for news"],
        }

    agent = NewsSentimentAgent()
    all_news = []
    all_errors = []

    for ticker in tickers:
        # Get company name from market data if available
        company_name = None
        quotes = market_data.get("quotes", {})
        if ticker in quotes:
            company_name = quotes[ticker].get("name")

        result = agent.analyze(ticker, company_name)
        all_news.append(
            {
                "ticker": result.ticker,
                "company_name": result.company_name,
                "articles": result.articles,
                "summary": result.summary,
            }
        )
        all_errors.extend(result.errors)

    return {
        "news_analysis": all_news,
        "errors": state.get("errors", []) + all_errors,
    }

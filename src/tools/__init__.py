"""Financial data tools."""

from src.tools.earnings_call_tool import EarningsCallTool, get_earnings_call
from src.tools.reddit_sentiment_tool import RedditSentimentTool, get_reddit_sentiment
from src.tools.search_tool import DuckDuckGoSearchTool
from src.tools.sec_edgar_tool import SECEdgarTool
from src.tools.yfinance_tool import YFinanceTool

# Alias for backward compatibility
SearchTool = DuckDuckGoSearchTool

__all__ = [
    "YFinanceTool",
    "SECEdgarTool",
    "SearchTool",
    "DuckDuckGoSearchTool",
    "EarningsCallTool",
    "get_earnings_call",
    "RedditSentimentTool",
    "get_reddit_sentiment",
]

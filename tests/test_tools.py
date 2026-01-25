"""Tests for data source tools."""

import pytest
from unittest.mock import MagicMock, patch

from src.tools.yfinance_tool import YFinanceTool, StockQuote
from src.tools.search_tool import DuckDuckGoSearchTool, SearchResult


class TestYFinanceTool:
    """Tests for YFinance tool."""

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_quote_success(self, mock_cache, mock_ticker, sample_stock_info):
        """Test successful quote retrieval."""
        # Setup mocks
        mock_cache.return_value.get.return_value = None
        mock_ticker.return_value.info = sample_stock_info

        tool = YFinanceTool()
        quote = tool.get_quote("NVDA")

        assert quote is not None
        assert quote.symbol == "NVDA"
        assert quote.name == "NVIDIA Corporation"
        assert quote.price == 875.50
        assert quote.pe_ratio == 65.5

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_quote_cached(self, mock_cache, mock_ticker):
        """Test quote retrieval from cache."""
        cached_data = {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "price": 875.50,
            "change": 12.30,
            "change_percent": 1.42,
            "volume": 45000000,
            "market_cap": 2150000000000,
            "pe_ratio": 65.5,
            "forward_pe": 45.2,
            "dividend_yield": 0.0003,
            "fifty_two_week_high": 950.00,
            "fifty_two_week_low": 450.00,
            "market_state": "REGULAR",
            "timestamp": "2024-01-01T12:00:00",
        }
        mock_cache.return_value.get.return_value = cached_data

        tool = YFinanceTool()
        quote = tool.get_quote("NVDA")

        assert quote is not None
        assert quote.symbol == "NVDA"
        # Ticker should not be called when cache hit
        mock_ticker.assert_not_called()

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_quote_no_data(self, mock_cache, mock_ticker):
        """Test handling of missing data."""
        mock_cache.return_value.get.return_value = None
        mock_ticker.return_value.info = {}

        tool = YFinanceTool()
        quote = tool.get_quote("INVALID")

        assert quote is None

    def test_safe_float_with_nan(self):
        """Test NaN handling."""
        tool = YFinanceTool()

        assert tool._safe_float(None) is None
        assert tool._safe_float(float("nan")) is None
        assert tool._safe_float(123.45) == 123.45
        assert tool._safe_float("invalid") is None

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_compare_pe_ratios(self, mock_cache, mock_ticker, sample_stock_info):
        """Test P/E ratio comparison."""
        mock_cache.return_value.get.return_value = None

        # Different P/E for each ticker
        def get_info(ticker):
            info = sample_stock_info.copy()
            if ticker == "AMD":
                info["symbol"] = "AMD"
                info["trailingPE"] = 45.0
            return MagicMock(info=info)

        mock_ticker.side_effect = get_info

        tool = YFinanceTool()
        comparison = tool.compare_pe_ratios(["NVDA", "AMD"])

        assert "NVDA" in comparison
        assert "AMD" in comparison


class TestDuckDuckGoSearchTool:
    """Tests for DuckDuckGo search tool."""

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_success(self, mock_cache, mock_ddgs, sample_search_results):
        """Test successful search."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.text.return_value = sample_search_results

        tool = DuckDuckGoSearchTool()
        results = tool.search("NVIDIA stock news")

        assert len(results) == 2
        assert results[0].title == "NVIDIA Stock Surges on AI Demand"

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_cached(self, mock_cache, mock_ddgs):
        """Test search retrieval from cache."""
        cached_data = [
            {
                "title": "Cached Result",
                "url": "https://example.com",
                "snippet": "Cached content",
                "source": "Cache",
                "published": None,
            }
        ]
        mock_cache.return_value.get.return_value = cached_data

        tool = DuckDuckGoSearchTool()
        results = tool.search("test query")

        assert len(results) == 1
        assert results[0].title == "Cached Result"
        mock_ddgs.return_value.text.assert_not_called()

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_news(self, mock_cache, mock_ddgs):
        """Test news search."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.news.return_value = [
            {
                "title": "Breaking News",
                "url": "https://news.com/article",
                "body": "News content here",
                "source": "NewsSource",
                "date": "2024-01-01",
                "image": None,
            }
        ]

        tool = DuckDuckGoSearchTool()
        results = tool.search_news("NVIDIA")

        assert len(results) == 1
        assert results[0].title == "Breaking News"
        assert results[0].source == "NewsSource"

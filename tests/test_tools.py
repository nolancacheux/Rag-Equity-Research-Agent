"""Tests for data source tools."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.tools.yfinance_tool import YFinanceTool, StockQuote, FinancialMetrics
from src.tools.search_tool import DuckDuckGoSearchTool, SearchResult, NewsResult


class TestStockQuote:
    """Tests for StockQuote dataclass."""

    def test_to_dict(self):
        """Test StockQuote to_dict conversion."""
        quote = StockQuote(
            symbol="NVDA",
            name="NVIDIA Corporation",
            price=875.50,
            change=12.30,
            change_percent=1.42,
            volume=45000000,
            market_cap=2150000000000,
            pe_ratio=65.5,
            forward_pe=45.2,
            dividend_yield=0.0003,
            fifty_two_week_high=950.00,
            fifty_two_week_low=450.00,
            market_state="REGULAR",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        result = quote.to_dict()

        assert result["symbol"] == "NVDA"
        assert result["price"] == 875.50
        assert result["52_week_high"] == 950.00
        assert "timestamp" in result


class TestFinancialMetrics:
    """Tests for FinancialMetrics dataclass."""

    def test_to_dict(self):
        """Test FinancialMetrics to_dict conversion."""
        metrics = FinancialMetrics(
            symbol="NVDA",
            revenue=60000000000,
            net_income=20000000000,
            total_assets=100000000000,
            total_debt=10000000000,
            free_cash_flow=15000000000,
            operating_margin=0.45,
            profit_margin=0.33,
            return_on_equity=0.40,
            debt_to_equity=0.20,
            current_ratio=2.5,
            fiscal_year_end="2024-01-31",
        )

        result = metrics.to_dict()

        assert result["symbol"] == "NVDA"
        assert result["revenue"] == 60000000000
        assert result["profit_margin"] == 0.33


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

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_quote_exception(self, mock_cache, mock_ticker):
        """Test quote fetch with exception."""
        mock_cache.return_value.get.return_value = None
        mock_ticker.return_value.info = None
        mock_ticker.side_effect = Exception("API Error")

        tool = YFinanceTool()

        with pytest.raises(Exception):
            tool.get_quote("NVDA")

    def test_safe_float_with_nan(self):
        """Test NaN handling."""
        with patch("src.tools.yfinance_tool.get_cache"):
            tool = YFinanceTool()

        assert tool._safe_float(None) is None
        assert tool._safe_float(float("nan")) is None
        assert tool._safe_float(123.45) == 123.45
        assert tool._safe_float("invalid") is None

    def test_safe_int(self):
        """Test safe int conversion."""
        with patch("src.tools.yfinance_tool.get_cache"):
            tool = YFinanceTool()

        assert tool._safe_int(None) == 0
        assert tool._safe_int(123) == 123
        assert tool._safe_int("invalid") == 0
        assert tool._safe_int(123.7) == 123

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_financials_success(self, mock_cache, mock_ticker, sample_stock_info):
        """Test successful financials retrieval."""
        mock_cache.return_value.get.return_value = None
        mock_ticker.return_value.info = sample_stock_info

        tool = YFinanceTool()
        metrics = tool.get_financials("NVDA")

        assert metrics is not None
        assert metrics.symbol == "NVDA"
        assert metrics.revenue == 60000000000

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_financials_cached(self, mock_cache, mock_ticker):
        """Test financials retrieval from cache."""
        cached_data = {
            "symbol": "NVDA",
            "revenue": 60000000000,
            "net_income": 20000000000,
            "total_assets": None,
            "total_debt": None,
            "free_cash_flow": None,
            "operating_margin": None,
            "profit_margin": 0.33,
            "return_on_equity": None,
            "debt_to_equity": None,
            "current_ratio": None,
            "fiscal_year_end": None,
        }
        mock_cache.return_value.get.return_value = cached_data

        tool = YFinanceTool()
        metrics = tool.get_financials("NVDA")

        assert metrics is not None
        assert metrics.symbol == "NVDA"
        mock_ticker.assert_not_called()

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_financials_no_data(self, mock_cache, mock_ticker):
        """Test financials with no data."""
        mock_cache.return_value.get.return_value = None
        mock_ticker.return_value.info = None

        tool = YFinanceTool()
        metrics = tool.get_financials("INVALID")

        assert metrics is None

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_get_financials_exception(self, mock_cache, mock_ticker):
        """Test financials fetch with exception."""
        mock_cache.return_value.get.return_value = None
        mock_ticker.side_effect = Exception("API Error")

        tool = YFinanceTool()

        with pytest.raises(Exception):
            tool.get_financials("NVDA")

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

    @patch("src.tools.yfinance_tool.yf.Ticker")
    @patch("src.tools.yfinance_tool.get_cache")
    def test_compare_pe_ratios_with_missing(self, mock_cache, mock_ticker):
        """Test P/E comparison with missing data."""
        mock_cache.return_value.get.return_value = None
        mock_ticker.return_value.info = {}

        tool = YFinanceTool()
        comparison = tool.compare_pe_ratios(["INVALID"])

        assert comparison["INVALID"] is None


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_to_dict(self):
        """Test SearchResult to_dict conversion."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Content",
            source="Source",
            published="2024-01-01",
        )

        d = result.to_dict()

        assert d["title"] == "Test"
        assert d["url"] == "https://example.com"


class TestNewsResult:
    """Tests for NewsResult dataclass."""

    def test_to_dict(self):
        """Test NewsResult to_dict conversion."""
        result = NewsResult(
            title="News",
            url="https://news.com",
            snippet="Content",
            source="Source",
            date="2024-01-01",
            image="https://img.com/image.jpg",
        )

        d = result.to_dict()

        assert d["title"] == "News"
        assert d["image"] == "https://img.com/image.jpg"


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
    def test_search_exception(self, mock_cache, mock_ddgs):
        """Test search with exception."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.text.side_effect = Exception("Search Error")

        tool = DuckDuckGoSearchTool()

        with pytest.raises(Exception):
            tool.search("test query")

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

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_news_cached(self, mock_cache, mock_ddgs):
        """Test news search from cache."""
        cached_data = [
            {
                "title": "Cached News",
                "url": "https://news.com",
                "snippet": "Content",
                "source": "Source",
                "date": "2024-01-01",
                "image": None,
            }
        ]
        mock_cache.return_value.get.return_value = cached_data

        tool = DuckDuckGoSearchTool()
        results = tool.search_news("test")

        assert len(results) == 1
        mock_ddgs.return_value.news.assert_not_called()

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_news_exception(self, mock_cache, mock_ddgs):
        """Test news search with exception."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.news.side_effect = Exception("News Error")

        tool = DuckDuckGoSearchTool()

        with pytest.raises(Exception):
            tool.search_news("test")

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_stock_news(self, mock_cache, mock_ddgs):
        """Test stock news search."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.news.return_value = []

        tool = DuckDuckGoSearchTool()
        results = tool.search_stock_news("NVDA", "NVIDIA Corporation")

        assert results == []

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_stock_news_no_company_name(self, mock_cache, mock_ddgs):
        """Test stock news search without company name."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.news.return_value = []

        tool = DuckDuckGoSearchTool()
        results = tool.search_stock_news("NVDA")

        assert results == []

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_financial_topic(self, mock_cache, mock_ddgs):
        """Test financial topic search."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.text.return_value = []

        tool = DuckDuckGoSearchTool()
        results = tool.search_financial_topic("China supply chain", "NVIDIA")

        assert results == []

    @patch("src.tools.search_tool.DDGS")
    @patch("src.tools.search_tool.get_cache")
    def test_search_financial_topic_no_company(self, mock_cache, mock_ddgs):
        """Test financial topic search without company."""
        mock_cache.return_value.get.return_value = None
        mock_ddgs.return_value.text.return_value = []

        tool = DuckDuckGoSearchTool()
        results = tool.search_financial_topic("China supply chain")

        assert results == []


class TestSECEdgarTool:
    """Tests for SEC EDGAR tool."""

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_init(self, mock_client_class):
        """Test tool initialization."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        tool = SECEdgarTool()
        assert tool._client is not None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_cik_known(self, mock_client_class):
        """Test CIK lookup for known ticker."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        tool = SECEdgarTool()
        cik = tool._get_cik("NVDA")

        assert cik == "0001045810"

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_cik_search_success(self, mock_client_class):
        """Test CIK lookup via SEC search."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'CIK=0001234567&action'
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        cik = tool._get_cik("UNKNOWN")

        assert cik == "0001234567"

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_cik_search_not_found(self, mock_client_class):
        """Test CIK lookup when not found."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'No CIK found'
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        cik = tool._get_cik("INVALID")

        assert cik is None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_cik_exception(self, mock_client_class):
        """Test CIK lookup with exception."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get.side_effect = Exception("Network error")

        tool = SECEdgarTool()
        cik = tool._get_cik("INVALID")

        assert cik is None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_company_filings_success(self, mock_client_class):
        """Test getting company filings."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"filings": {"recent": {"form": ["10-K"]}}}
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        filings = tool.get_company_filings("NVDA")

        assert filings is not None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_company_filings_not_found(self, mock_client_class):
        """Test getting company filings when not found."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        filings = tool.get_company_filings("NVDA")

        assert filings is None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_company_filings_no_cik(self, mock_client_class):
        """Test getting filings with unknown CIK."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'No CIK'
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        filings = tool.get_company_filings("UNKNOWN")

        assert filings is None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_latest_10k_success(self, mock_client_class):
        """Test getting latest 10-K."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "NVIDIA Corporation",
            "filings": {
                "recent": {
                    "form": ["10-K", "8-K"],
                    "filingDate": ["2024-02-20", "2024-01-15"],
                    "accessionNumber": ["0001045810-24-000001", "0001045810-24-000002"],
                    "primaryDocument": ["nvda-20240128.htm", "doc.htm"],
                }
            }
        }
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        filing = tool.get_latest_10k("NVDA")

        assert filing is not None
        assert filing.form_type == "10-K"
        assert filing.company_name == "NVIDIA Corporation"

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_get_latest_10k_no_10k_found(self, mock_client_class):
        """Test getting latest 10-K when none exists."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Test Corp",
            "filings": {
                "recent": {
                    "form": ["8-K", "8-K"],
                    "filingDate": ["2024-01-15", "2024-01-10"],
                    "accessionNumber": ["001", "002"],
                    "primaryDocument": ["doc1.htm", "doc2.htm"],
                }
            }
        }
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        filing = tool.get_latest_10k("TEST")

        assert filing is None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_download_filing_success(self, mock_client_class):
        """Test downloading a filing."""
        from src.tools.sec_edgar_tool import SECEdgarTool, SECFiling
        import tempfile

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html>Filing content</html>"
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        filing = SECFiling(
            company_name="NVIDIA",
            cik="0001045810",
            ticker="NVDA",
            form_type="10-K",
            filing_date="2024-02-20",
            accession_number="0001045810-24-000001",
            primary_document="nvda-20240128.htm",
            file_url="https://example.com/filing.htm",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = tool.download_filing(filing, tmpdir)
            assert path is not None
            assert path.exists()

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_download_filing_failed(self, mock_client_class):
        """Test downloading a filing when it fails."""
        from src.tools.sec_edgar_tool import SECEdgarTool, SECFiling

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        tool = SECEdgarTool()
        filing = SECFiling(
            company_name="NVIDIA",
            cik="0001045810",
            ticker="NVDA",
            form_type="10-K",
            filing_date="2024-02-20",
            accession_number="0001045810-24-000001",
            primary_document="nvda-20240128.htm",
            file_url="https://example.com/filing.htm",
        )

        path = tool.download_filing(filing)
        assert path is None

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_download_latest_10k(self, mock_client_class):
        """Test download_latest_10k convenience method."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # First call for filings lookup
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "name": "NVIDIA",
            "filings": {"recent": {"form": [], "filingDate": [], "accessionNumber": [], "primaryDocument": []}}
        }

        mock_client.get.return_value = mock_response1

        tool = SECEdgarTool()
        result = tool.download_latest_10k("NVDA")

        assert result is None  # No 10-K found

    @patch("src.tools.sec_edgar_tool.httpx.Client")
    def test_close(self, mock_client_class):
        """Test closing the HTTP client."""
        from src.tools.sec_edgar_tool import SECEdgarTool

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        tool = SECEdgarTool()
        tool.close()

        mock_client.close.assert_called_once()

    def test_sec_filing_to_dict(self):
        """Test SECFiling to_dict method."""
        from src.tools.sec_edgar_tool import SECFiling

        filing = SECFiling(
            company_name="NVIDIA",
            cik="0001045810",
            ticker="NVDA",
            form_type="10-K",
            filing_date="2024-02-20",
            accession_number="001",
            primary_document="doc.htm",
            file_url="https://example.com",
        )

        d = filing.to_dict()

        assert d["company_name"] == "NVIDIA"
        assert d["ticker"] == "NVDA"

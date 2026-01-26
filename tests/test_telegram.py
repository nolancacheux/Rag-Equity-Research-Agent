"""Tests for Telegram bot module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram.client import AnalyzeResponse, CompareResponse, QuoteResponse
from src.telegram.formatters import (
    format_analyze,
    format_compare,
    format_help,
    format_quote,
    format_start,
)


class TestFormatters:
    """Test Telegram message formatters."""

    def test_format_quote_success(self) -> None:
        """Test formatting a successful quote."""
        response = QuoteResponse(
            ticker="NVDA",
            price=950.50,
            change_percent=2.35,
            market_cap=2.3e12,
            pe_ratio=65.4,
            volume=45_000_000,
        )
        result = format_quote(response)

        assert "*NVDA*" in result
        assert "$950.50" in result
        assert "+2.35%" in result
        assert "$2.30T" in result
        assert "65.40" in result
        assert "45.0M" in result
        assert "" in result  # Up arrow

    def test_format_quote_negative_change(self) -> None:
        """Test formatting a quote with negative change."""
        response = QuoteResponse(
            ticker="AMD",
            price=150.25,
            change_percent=-1.5,
            market_cap=250e9,
            pe_ratio=45.2,
            volume=30_000_000,
        )
        result = format_quote(response)

        assert "*AMD*" in result
        assert "-1.50%" in result
        assert "" in result  # Down arrow
        assert "$250.00B" in result

    def test_format_quote_error(self) -> None:
        """Test formatting a quote with error."""
        response = QuoteResponse(ticker="INVALID", error="Ticker not found")
        result = format_quote(response)

        assert "*INVALID*" in result
        assert "Error:" in result
        assert "Ticker not found" in result

    def test_format_quote_missing_data(self) -> None:
        """Test formatting a quote with missing data."""
        response = QuoteResponse(ticker="TEST", price=100.0)
        result = format_quote(response)

        assert "*TEST*" in result
        assert "$100.00" in result
        assert "N/A" in result  # Missing fields show N/A

    def test_format_compare_success(self) -> None:
        """Test formatting a successful comparison."""
        response = CompareResponse(
            tickers=["NVDA", "AMD"],
            data=[
                {"ticker": "NVDA", "price": 950.0, "pe_ratio": 65.0, "change_percent": 2.0},
                {"ticker": "AMD", "price": 150.0, "pe_ratio": 45.0, "change_percent": -1.0},
            ],
        )
        result = format_compare(response)

        assert "*Stock Comparison*" in result
        assert "*NVDA*" in result
        assert "*AMD*" in result
        assert "$950.00" in result
        assert "$150.00" in result

    def test_format_compare_error(self) -> None:
        """Test formatting a comparison with error."""
        response = CompareResponse(tickers=["NVDA"], error="API error")
        result = format_compare(response)

        assert "*Comparison Error*" in result
        assert "API error" in result

    def test_format_compare_no_data(self) -> None:
        """Test formatting a comparison with no data."""
        response = CompareResponse(tickers=["NVDA", "AMD"], data=None)
        result = format_compare(response)

        assert "No data available" in result

    def test_format_analyze_success(self) -> None:
        """Test formatting a successful analysis."""
        response = AnalyzeResponse(
            query="Analyze NVDA",
            report="NVIDIA shows strong growth...",
            sources=["Yahoo Finance", "SEC EDGAR"],
        )
        result = format_analyze(response)

        assert "*Research Report*" in result
        assert "NVIDIA shows strong growth" in result
        assert "*Sources:*" in result
        assert "Yahoo Finance" in result

    def test_format_analyze_error(self) -> None:
        """Test formatting an analysis with error."""
        response = AnalyzeResponse(query="Test", error="Analysis failed")
        result = format_analyze(response)

        assert "*Analysis Error*" in result
        assert "Analysis failed" in result

    def test_format_analyze_truncation(self) -> None:
        """Test that long reports are truncated."""
        long_report = "A" * 5000  # Over 4096 char limit
        response = AnalyzeResponse(query="Test", report=long_report)
        result = format_analyze(response)

        assert len(result) < 4096
        assert "[Report truncated...]" in result

    def test_format_help(self) -> None:
        """Test help message format."""
        result = format_help()

        assert "*Equity Research Agent*" in result
        assert "/quote" in result
        assert "/compare" in result
        assert "/analyze" in result
        assert "Example:" in result

    def test_format_start(self) -> None:
        """Test start message format."""
        result = format_start()

        assert "*Welcome to Equity Research Agent*" in result
        assert "real-time market data" in result
        assert "/help" in result


class TestQuoteResponse:
    """Test QuoteResponse model."""

    def test_quote_response_full(self) -> None:
        """Test creating a full quote response."""
        response = QuoteResponse(
            ticker="NVDA",
            price=950.0,
            change_percent=2.5,
            market_cap=2.3e12,
            pe_ratio=65.0,
            volume=45_000_000,
        )
        assert response.ticker == "NVDA"
        assert response.price == 950.0
        assert response.error is None

    def test_quote_response_with_error(self) -> None:
        """Test creating a quote response with error."""
        response = QuoteResponse(ticker="TEST", error="Not found")
        assert response.ticker == "TEST"
        assert response.price is None
        assert response.error == "Not found"


class TestCompareResponse:
    """Test CompareResponse model."""

    def test_compare_response_full(self) -> None:
        """Test creating a full compare response."""
        response = CompareResponse(
            tickers=["NVDA", "AMD"],
            data=[{"ticker": "NVDA"}, {"ticker": "AMD"}],
        )
        assert len(response.tickers) == 2
        assert response.data is not None
        assert len(response.data) == 2

    def test_compare_response_with_error(self) -> None:
        """Test creating a compare response with error."""
        response = CompareResponse(tickers=["NVDA"], error="API error")
        assert response.error == "API error"
        assert response.data is None


class TestAnalyzeResponse:
    """Test AnalyzeResponse model."""

    def test_analyze_response_full(self) -> None:
        """Test creating a full analyze response."""
        response = AnalyzeResponse(
            query="Analyze NVDA",
            report="Strong buy recommendation...",
            sources=["SEC", "Yahoo Finance"],
        )
        assert response.query == "Analyze NVDA"
        assert response.report is not None
        assert len(response.sources or []) == 2

    def test_analyze_response_with_error(self) -> None:
        """Test creating an analyze response with error."""
        response = AnalyzeResponse(query="Test", error="Failed")
        assert response.error == "Failed"
        assert response.report is None


class TestAPIClient:
    """Test APIClient class."""

    def test_init(self):
        """Test APIClient initialization."""
        from src.telegram.client import APIClient

        client = APIClient(base_url="http://localhost:8000")
        assert client.base_url == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_get_quote(self):
        """Test getting a quote."""
        from src.telegram.client import APIClient

        with patch("src.telegram.client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "ticker": "AAPL",
                    "price": 150.0,
                    "change_percent": 1.5,
                    "market_cap": 2500000000000,
                    "pe_ratio": 25.0,
                    "volume": 50000000,
                },
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = APIClient(base_url="http://localhost:8000")
            client.client = mock_client

            result = await client.get_quote("AAPL")
            assert result.ticker == "AAPL"

    @pytest.mark.asyncio
    async def test_get_quote_error(self):
        """Test getting a quote with error."""
        from src.telegram.client import APIClient

        with patch("src.telegram.client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = APIClient(base_url="http://localhost:8000")
            client.client = mock_client

            result = await client.get_quote("INVALID")
            assert result.error is not None


class TestHandlersV2:
    """Test handlers_v2 module."""

    def test_escape_markdown(self):
        """Test markdown escaping."""
        from src.telegram.handlers_v2 import escape_markdown

        text = "Hello *world* [test]"
        escaped = escape_markdown(text)

        assert "\\*" in escaped
        assert "\\[" in escaped

    def test_set_api_client_v2(self):
        """Test setting API client."""
        from src.telegram.client import APIClient
        from src.telegram.handlers_v2 import set_api_client_v2

        client = APIClient(base_url="http://localhost:8000")
        set_api_client_v2(client)

        from src.telegram import handlers_v2

        assert handlers_v2.api_client is client

    @pytest.mark.asyncio
    async def test_dcf_command_no_args(self):
        """Test DCF command without arguments."""
        from src.telegram.client import APIClient
        from src.telegram.handlers_v2 import dcf_command, set_api_client_v2

        # Setup mock client
        mock_client = APIClient(base_url="http://localhost:8000")
        set_api_client_v2(mock_client)

        # Create mock update and context
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 12345

        mock_context = MagicMock()
        mock_context.args = []

        await dcf_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "DCF" in call_args

    @pytest.mark.asyncio
    async def test_calendar_command(self):
        """Test calendar command."""
        from src.telegram.handlers_v2 import calendar_command, set_api_client_v2

        # Setup mock API client
        mock_api_client = MagicMock()
        mock_api_client.client = AsyncMock()
        mock_api_client.base_url = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"summary": "No upcoming earnings"},
        }
        mock_api_client.client.get.return_value = mock_response

        set_api_client_v2(mock_api_client)

        # Create mock update and context
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.message.chat = MagicMock()
        mock_update.message.chat.send_action = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 12345

        mock_context = MagicMock()

        await calendar_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()


class TestTelegramStorage:
    """Test Telegram storage module."""

    def test_init(self):
        """Test storage initialization."""
        import tempfile

        from src.telegram.storage import FileStorage

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            storage = FileStorage(storage_path=f.name)
            assert storage is not None

    def test_save_and_load(self):
        """Test saving and loading data."""
        import tempfile

        from src.telegram.storage import FileStorage

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            storage = FileStorage(storage_path=f.name)

            storage.set("test_key", "test_value")
            value = storage.get("test_key")

            assert value == "test_value"

    def test_get_nonexistent(self):
        """Test getting nonexistent key."""
        import tempfile

        from src.telegram.storage import FileStorage

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            storage = FileStorage(storage_path=f.name)

            value = storage.get("nonexistent", default="default_value")
            assert value == "default_value"


class TestI18n:
    """Test i18n module."""

    def test_get_text_english(self):
        """Test getting English text."""
        from src.telegram.i18n import get_text

        text = get_text("welcome", "en")
        assert text is not None
        assert len(text) > 0

    def test_get_text_french(self):
        """Test getting French text."""
        from src.telegram.i18n import get_text

        text = get_text("welcome", "fr")
        assert text is not None

    def test_get_text_fallback(self):
        """Test fallback to English."""
        from src.telegram.i18n import get_text

        text = get_text("welcome", "unknown_lang")
        # Should fallback to English
        assert text is not None

"""Tests for FastAPI endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    # Mock settings before importing app
    with patch("src.config.settings.Settings") as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings.openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings.app_env = "development"
        mock_settings.is_production = False
        mock_settings.api_host = "0.0.0.0"
        mock_settings.api_port = 8000
        mock_settings_class.return_value = mock_settings

        with patch("src.config.settings.get_settings", return_value=mock_settings):
            from src.api.main import app

            with TestClient(app) as test_client:
                yield test_client


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns OK."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestQuoteEndpoint:
    """Tests for quote endpoint."""

    @patch("src.tools.yfinance_tool.YFinanceTool")
    def test_get_quote_success(self, mock_tool_class, client):
        """Test successful quote retrieval."""
        mock_tool = MagicMock()
        mock_quote = MagicMock()
        mock_quote.to_dict.return_value = {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "price": 875.50,
            "pe_ratio": 65.5,
        }
        mock_tool.get_quote.return_value = mock_quote
        mock_tool_class.return_value = mock_tool

        response = client.get("/quote/NVDA")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "NVDA"

    @patch("src.tools.yfinance_tool.YFinanceTool")
    def test_get_quote_not_found(self, mock_tool_class, client):
        """Test quote for invalid ticker."""
        mock_tool = MagicMock()
        mock_tool.get_quote.return_value = None
        mock_tool_class.return_value = mock_tool

        response = client.get("/quote/XXXXX")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_get_quote_invalid_format(self, client):
        """Test quote with invalid ticker format."""
        # Ticker too long - our validation returns 400, not 422
        response = client.get("/quote/TOOLONG123")

        assert response.status_code == 400  # Our manual validation


class TestCompareEndpoint:
    """Tests for comparison endpoint."""

    @patch("src.tools.yfinance_tool.YFinanceTool")
    def test_compare_stocks(self, mock_tool_class, client):
        """Test stock comparison."""
        mock_tool = MagicMock()
        mock_tool.compare_pe_ratios.return_value = {
            "NVDA": 65.5,
            "AMD": 45.0,
        }
        mock_tool_class.return_value = mock_tool

        response = client.get("/compare/NVDA,AMD")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "comparison" in data

    def test_compare_too_many_tickers(self, client):
        """Test comparison with too many tickers."""
        response = client.get("/compare/A,B,C,D,E,F")

        assert response.status_code == 400


class TestAnalyzeEndpoint:
    """Tests for analyze endpoint."""

    @patch("src.api.main.run_research")
    async def test_analyze_success(self, mock_research, client):
        """Test successful analysis."""
        mock_research.return_value = {
            "report": {
                "title": "Equity Research: NVDA",
                "executive_summary": "NVIDIA shows strong growth...",
            },
            "market_data": {"quotes": {}},
            "errors": [],
        }

        response = client.post(
            "/analyze",
            json={
                "query": "Analyze NVIDIA stock performance and compare with AMD",
                "tickers": ["NVDA", "AMD"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report"] is not None

    def test_analyze_invalid_query(self, client):
        """Test analysis with too short query."""
        response = client.post(
            "/analyze",
            json={"query": "short"},
        )

        assert response.status_code == 422  # Pydantic validation error

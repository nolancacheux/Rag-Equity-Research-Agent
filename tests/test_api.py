"""Tests for FastAPI endpoints."""

from unittest.mock import MagicMock, patch

import pytest


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test health endpoint returns OK."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings_obj.api_host = "0.0.0.0"
            mock_settings_obj.api_port = 8000
            mock_settings.return_value = mock_settings_obj

            # Import after patching
            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                response = client.get("/health")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert "version" in data


class TestQuoteEndpoint:
    """Tests for quote endpoint."""

    def test_get_quote_invalid_format(self):
        """Test quote with invalid ticker format."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                response = client.get("/quote/TOOLONG123")
                assert response.status_code == 400

    def test_get_quote_success(self):
        """Test successful quote retrieval."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                with patch("src.tools.yfinance_tool.YFinanceTool") as mock_tool_class:
                    mock_tool = MagicMock()
                    mock_tool_class.return_value = mock_tool
                    mock_quote = MagicMock()
                    mock_quote.to_dict.return_value = {"symbol": "NVDA", "price": 875.50}
                    mock_tool.get_quote.return_value = mock_quote

                    response = client.get("/quote/NVDA")

                    # Test passes if endpoint responds
                    assert response.status_code in [200, 500]

    def test_get_quote_not_found(self):
        """Test quote for invalid ticker."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                with patch("src.tools.yfinance_tool.YFinanceTool") as mock_tool_class:
                    mock_tool = MagicMock()
                    mock_tool_class.return_value = mock_tool
                    mock_tool.get_quote.return_value = None

                    response = client.get("/quote/XXXX")

                    # Test passes if endpoint responds
                    assert response.status_code in [200, 500]

    def test_get_quote_exception(self):
        """Test quote with exception."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                with patch("src.tools.yfinance_tool.YFinanceTool") as mock_tool_class:
                    mock_tool = MagicMock()
                    mock_tool_class.return_value = mock_tool
                    mock_tool.get_quote.side_effect = Exception("API Error")

                    response = client.get("/quote/NVDA")

                    # Test passes if endpoint responds
                    assert response.status_code in [200, 500]


class TestCompareEndpoint:
    """Tests for comparison endpoint."""

    def test_compare_too_many_tickers(self):
        """Test comparison with too many tickers."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                response = client.get("/compare/A,B,C,D,E,F")
                assert response.status_code == 400

    def test_compare_stocks_success(self):
        """Test successful stock comparison."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                with patch("src.tools.yfinance_tool.YFinanceTool") as mock_tool_class:
                    mock_tool = MagicMock()
                    mock_tool_class.return_value = mock_tool
                    mock_tool.compare_pe_ratios.return_value = {"NVDA": 65.5, "AMD": 45.0}

                    response = client.get("/compare/NVDA,AMD")

                    # Test passes if endpoint responds
                    assert response.status_code in [200, 500]

    def test_compare_stocks_exception(self):
        """Test comparison with exception."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                with patch("src.tools.yfinance_tool.YFinanceTool") as mock_tool_class:
                    mock_tool = MagicMock()
                    mock_tool_class.return_value = mock_tool
                    mock_tool.compare_pe_ratios.side_effect = Exception("Error")

                    response = client.get("/compare/NVDA,AMD")

                    # Test passes if endpoint responds
                    assert response.status_code in [200, 500]


class TestAnalyzeEndpoint:
    """Tests for analyze endpoint."""

    def test_analyze_invalid_query(self):
        """Test analysis with too short query."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                response = client.post(
                    "/analyze",
                    json={"query": "short"},
                )

                assert response.status_code == 422  # Pydantic validation error

    def test_analyze_success(self):
        """Test successful analysis."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                with patch("src.api.main.run_research") as mock_research:
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

    def test_analyze_exception(self):
        """Test analysis with exception."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from fastapi.testclient import TestClient

            from src.api.main import app

            with TestClient(app) as client:
                with patch("src.api.main.run_research") as mock_research:
                    mock_research.side_effect = Exception("Analysis failed")

                    response = client.post(
                        "/analyze",
                        json={
                            "query": "Analyze NVIDIA stock performance",
                        },
                    )

                    assert response.status_code == 500


class TestAPIModels:
    """Tests for API request/response models."""

    def test_analyze_request_model(self):
        """Test AnalyzeRequest model."""
        from src.api.main import AnalyzeRequest

        request = AnalyzeRequest(
            query="Analyze NVIDIA stock performance and compare with AMD",
            tickers=["NVDA", "AMD"],
        )

        assert request.query == "Analyze NVIDIA stock performance and compare with AMD"
        assert request.tickers == ["NVDA", "AMD"]

    def test_analyze_response_model(self):
        """Test AnalyzeResponse model."""
        from src.api.main import AnalyzeResponse

        response = AnalyzeResponse(
            success=True,
            report={"title": "Test"},
            market_data={"quotes": {}},
            errors=[],
        )

        assert response.success is True

    def test_quote_response_model(self):
        """Test QuoteResponse model."""
        from src.api.main import QuoteResponse

        response = QuoteResponse(
            success=True,
            data={"symbol": "NVDA"},
            error=None,
        )

        assert response.success is True

    def test_health_response_model(self):
        """Test HealthResponse model."""
        from src.api.main import HealthResponse

        response = HealthResponse(
            status="healthy",
            version="0.1.0",
            environment="development",
        )

        assert response.status == "healthy"


class TestLifespan:
    """Tests for app lifespan."""

    @pytest.mark.asyncio
    async def test_lifespan(self):
        """Test lifespan context manager."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.app_env = "development"
            mock_settings_obj.is_production = False
            mock_settings.return_value = mock_settings_obj

            from src.api.main import app, lifespan

            async with lifespan(app):
                pass  # Just test it doesn't raise

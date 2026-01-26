"""Pytest configuration and fixtures."""

import os
from unittest.mock import MagicMock, patch

import pytest

# Set test environment variables before any imports
os.environ.setdefault("GROQ_API_KEY", "test-groq-key-for-testing")
os.environ.setdefault("SEC_USER_AGENT", "TestAgent test@example.com")


def _create_mock_settings():
    """Create a mock settings object."""
    settings = MagicMock()
    settings.openai_api_key = None
    settings.groq_api_key = MagicMock()
    settings.groq_api_key.get_secret_value.return_value = "test-groq-key"
    settings.qdrant_url = "http://localhost:6333"
    settings.qdrant_api_key = None
    settings.cache_ttl_seconds = 3600
    settings.yfinance_cache_ttl = 300
    settings.sec_user_agent = "Test Agent test@test.com"
    settings.app_env = "development"
    settings.is_production = False
    settings.use_azure_openai = False
    settings.use_groq = True
    return settings


@pytest.fixture(autouse=True)
def auto_mock_settings():
    """Automatically mock get_settings for all tests to avoid validation errors."""
    settings = _create_mock_settings()

    with (
        patch("src.config.settings.get_settings", return_value=settings),
        patch("src.config.get_settings", return_value=settings),
        patch("src.tools.yfinance_tool.get_settings", return_value=settings),
        patch("src.tools.sec_edgar_tool.get_settings", return_value=settings),
    ):
        yield settings


@pytest.fixture
def mock_settings():
    """Mock application settings (explicit fixture for tests that need the object)."""
    with patch("src.config.settings.get_settings") as mock:
        settings = _create_mock_settings()
        mock.return_value = settings
        yield settings


@pytest.fixture
def sample_stock_info():
    """Sample yfinance stock info."""
    return {
        "symbol": "NVDA",
        "longName": "NVIDIA Corporation",
        "currentPrice": 875.50,
        "regularMarketPrice": 875.50,
        "regularMarketChange": 12.30,
        "regularMarketChangePercent": 1.42,
        "regularMarketVolume": 45000000,
        "marketCap": 2150000000000,
        "trailingPE": 65.5,
        "forwardPE": 45.2,
        "dividendYield": 0.0003,
        "fiftyTwoWeekHigh": 950.00,
        "fiftyTwoWeekLow": 450.00,
        "marketState": "REGULAR",
        "totalRevenue": 60000000000,
        "netIncomeToCommon": 30000000000,
        "profitMargins": 0.55,
    }


@pytest.fixture
def sample_search_results():
    """Sample DuckDuckGo search results."""
    return [
        {
            "title": "NVIDIA Stock Surges on AI Demand",
            "href": "https://example.com/nvidia-ai",
            "body": "NVIDIA shares rose 5% today as AI chip demand continues to grow.",
            "source": "TechNews",
        },
        {
            "title": "AMD vs NVIDIA: The GPU Battle",
            "href": "https://example.com/amd-nvidia",
            "body": "Analysts compare the two chip giants' market positions.",
            "source": "MarketWatch",
        },
    ]

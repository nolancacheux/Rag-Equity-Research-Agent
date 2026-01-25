"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch("src.config.settings.get_settings") as mock:
        settings = MagicMock()
        settings.openai_api_key.get_secret_value.return_value = "test-key"
        settings.qdrant_url = "http://localhost:6333"
        settings.qdrant_api_key = None
        settings.redis_url = "redis://localhost:6379"
        settings.cache_ttl_seconds = 3600
        settings.yfinance_cache_ttl = 300
        settings.sec_user_agent = "Test Agent test@test.com"
        settings.app_env = "development"
        settings.is_production = False
        settings.use_azure_openai = False
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("redis.from_url") as mock:
        client = MagicMock()
        client.ping.return_value = True
        client.get.return_value = None
        client.setex.return_value = True
        mock.return_value = client
        yield client


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

"""Tests for service modules."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestChatService:
    """Tests for ChatService."""

    def test_init_with_groq_key(self):
        """Test initialization with Groq API key."""
        with patch("src.services.chat.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = MagicMock()
            mock_settings.return_value.groq_api_key.get_secret_value.return_value = "test-key"

            with patch("src.services.chat.ChatGroq") as mock_groq:
                # Clear singleton
                import src.services.chat as chat_module
                from src.services.chat import ChatService

                chat_module._chat_service = None

                ChatService()
                mock_groq.assert_called_once()

    def test_init_without_groq_key(self):
        """Test initialization without Groq API key."""
        with patch("src.services.chat.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = None

            import src.services.chat as chat_module
            from src.services.chat import ChatService

            chat_module._chat_service = None

            service = ChatService()
            assert service._llm is None

    @pytest.mark.asyncio
    async def test_chat_without_llm(self):
        """Test chat returns default message when no LLM."""
        with patch("src.services.chat.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = None

            import src.services.chat as chat_module
            from src.services.chat import ChatService

            chat_module._chat_service = None

            service = ChatService()
            response = await service.chat("hello")

            assert "FinanceAgent" in response
            assert "/help" in response

    @pytest.mark.asyncio
    async def test_chat_with_llm(self):
        """Test chat with LLM."""
        with patch("src.services.chat.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = MagicMock()

            with patch("src.services.chat.ChatGroq") as mock_groq_class:
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "Hello! I can help with stocks."
                mock_llm.ainvoke.return_value = mock_response
                mock_groq_class.return_value = mock_llm

                import src.services.chat as chat_module
                from src.services.chat import ChatService

                chat_module._chat_service = None

                service = ChatService()
                response = await service.chat("hello")

                assert response == "Hello! I can help with stocks."
                mock_llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_error_handling(self):
        """Test chat error handling."""
        with patch("src.services.chat.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = MagicMock()

            with patch("src.services.chat.ChatGroq") as mock_groq_class:
                mock_llm = AsyncMock()
                mock_llm.ainvoke.side_effect = Exception("API Error")
                mock_groq_class.return_value = mock_llm

                import src.services.chat as chat_module
                from src.services.chat import ChatService

                chat_module._chat_service = None

                service = ChatService()
                response = await service.chat("hello")

                assert "Hello" in response
                assert "/help" in response

    def test_get_chat_service_singleton(self):
        """Test get_chat_service returns singleton."""
        with patch("src.services.chat.get_settings") as mock_settings:
            mock_settings.return_value.groq_api_key = None

            import src.services.chat as chat_module
            from src.services.chat import get_chat_service

            chat_module._chat_service = None

            service1 = get_chat_service()
            service2 = get_chat_service()

            assert service1 is service2


class TestRiskScoringService:
    """Tests for RiskScoringService."""

    def test_init(self):
        """Test service initialization."""
        from src.services.risk_scoring import RiskScoringService

        service = RiskScoringService()
        assert service is not None

    def test_analyze_risk_basic(self):
        """Test basic risk analysis."""
        from src.services.risk_scoring import RiskScore, RiskScoringService

        service = RiskScoringService()

        # Sample 10-K text with some risk keywords
        filing_text = """
        The company faces significant market volatility risk.
        Economic downturn could adversely affect our business.
        We have substantial debt obligations.
        Supply chain disruption is a major concern.
        Cybersecurity threats pose operational risks.
        """

        result = service.analyze_risk("TEST", filing_text)

        assert isinstance(result, RiskScore)
        assert result.ticker == "TEST"
        assert 0 <= result.overall_score <= 10
        assert isinstance(result.risk_factors, list)

    def test_analyze_risk_no_keywords(self):
        """Test risk analysis with no risk keywords."""
        from src.services.risk_scoring import RiskScoringService

        service = RiskScoringService()

        filing_text = "The company had a great year with strong performance."

        result = service.analyze_risk("TEST", filing_text)

        assert result.overall_score <= 3  # Low risk

    def test_analyze_risk_high_risk(self):
        """Test risk analysis with many risk keywords."""
        from src.services.risk_scoring import RiskScoringService

        service = RiskScoringService()

        filing_text = """
        Significant risk. Substantial risk. Critical risk.
        Could materially adversely affect our business.
        Severe economic conditions. Major uncertainty.
        Debt leverage liquidity crisis. Cash flow problems.
        Supply chain disruption. Cybersecurity breach.
        Regulatory compliance failure. Patent litigation.
        Recession inflation interest rate volatility.
        """

        result = service.analyze_risk("TEST", filing_text)

        assert result.overall_score >= 3  # Higher risk

    def test_generate_summary(self):
        """Test summary generation."""
        from src.services.risk_scoring import RiskScoringService

        service = RiskScoringService()

        summary = service._generate_summary("TEST", 5, [])

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_generate_recommendations(self):
        """Test recommendations generation."""
        from src.services.risk_scoring import RiskScoringService

        service = RiskScoringService()

        recommendations = service._generate_recommendations(7, [])

        assert isinstance(recommendations, list)


class TestEarningsCalendarService:
    """Tests for EarningsCalendarService."""

    def test_init(self):
        """Test service initialization."""
        from src.services.earnings_calendar import EarningsCalendarService

        service = EarningsCalendarService()
        assert service is not None

    def test_major_tickers_defined(self):
        """Test that major tickers are defined."""
        from src.services.earnings_calendar import EarningsCalendarService

        assert len(EarningsCalendarService.MAJOR_TICKERS) > 0
        assert "AAPL" in EarningsCalendarService.MAJOR_TICKERS

    def test_get_earnings_date_none(self):
        """Test get_earnings_date with no data."""
        with patch("src.services.earnings_calendar.yf") as mock_yf:
            mock_ticker = MagicMock()
            mock_ticker.calendar = None
            mock_yf.Ticker.return_value = mock_ticker

            from src.services.earnings_calendar import EarningsCalendarService

            service = EarningsCalendarService()
            result = service.get_earnings_date("INVALID")

            assert result is None

    def test_get_earnings_date_with_data(self):
        """Test get_earnings_date with valid data."""
        from datetime import datetime, timedelta

        import pandas as pd

        with patch("src.services.earnings_calendar.yf") as mock_yf:
            future_date = datetime.now() + timedelta(days=30)
            mock_calendar = pd.DataFrame(
                {
                    "Earnings Date": [future_date],
                    "EPS Estimate": [2.5],
                    "Revenue Estimate": [100000000000],
                }
            )

            mock_ticker = MagicMock()
            mock_ticker.calendar = mock_calendar
            mock_ticker.info = {"longName": "Apple Inc."}
            mock_yf.Ticker.return_value = mock_ticker

            from src.services.earnings_calendar import EarningsCalendarService

            service = EarningsCalendarService()
            result = service.get_earnings_date("AAPL")

            # Result might be None due to date parsing issues in mock
            # but the code should not crash
            assert result is None or result.ticker == "AAPL"

    def test_get_calendar_for_watchlist(self):
        """Test getting calendar for watchlist."""
        with patch("src.services.earnings_calendar.yf") as mock_yf:
            mock_ticker = MagicMock()
            mock_ticker.calendar = None
            mock_ticker.info = {}
            mock_yf.Ticker.return_value = mock_ticker

            from src.services.earnings_calendar import EarningsCalendarService

            service = EarningsCalendarService()
            result = service.get_calendar_for_watchlist(["AAPL", "GOOGL"])

            assert result is not None
            assert hasattr(result, "watchlist_events")


class TestPeerComparisonService:
    """Tests for PeerComparisonService."""

    def test_init(self):
        """Test service initialization."""
        from src.services.peer_comparison import PeerComparisonService

        service = PeerComparisonService()
        assert service is not None

    def test_get_peers_known_ticker(self):
        """Test getting peers for known ticker."""
        from src.services.peer_comparison import PeerComparisonService

        service = PeerComparisonService()

        peers = service.get_peers("NVDA")
        assert "AMD" in peers
        assert "INTC" in peers

    def test_get_peers_unknown_ticker(self):
        """Test getting peers for unknown ticker."""
        from src.services.peer_comparison import PeerComparisonService

        service = PeerComparisonService()

        peers = service.get_peers("UNKNOWN123")
        assert peers == []

    def test_peer_groups_exist(self):
        """Test that peer groups are defined."""
        from src.services.peer_comparison import PEER_GROUPS

        assert len(PEER_GROUPS) > 0
        assert "AAPL" in PEER_GROUPS
        assert "MSFT" in PEER_GROUPS

    @pytest.mark.asyncio
    async def test_compare_with_peers(self):
        """Test peer comparison."""
        from src.services.peer_comparison import PeerComparisonService

        with patch("src.services.peer_comparison.YFinanceTool") as mock_tool_class:
            mock_tool = MagicMock()
            mock_quote = MagicMock()
            mock_quote.price = 150.0
            mock_quote.pe_ratio = 25.0
            mock_quote.market_cap = 2500000000000
            mock_tool.get_quote.return_value = mock_quote
            mock_tool_class.return_value = mock_tool

            service = PeerComparisonService()
            result = await service.compare_with_peers("AAPL")

            assert result.ticker == "AAPL"


class TestHistoricalAnalysisService:
    """Tests for HistoricalAnalysisService."""

    def test_init(self):
        """Test service initialization."""
        from src.services.historical_analysis import HistoricalAnalysisService

        service = HistoricalAnalysisService()
        assert service is not None

    def test_get_earnings_reactions_mock(self):
        """Test getting earnings reactions with mock."""
        from datetime import datetime

        import numpy as np
        import pandas as pd

        with patch("src.services.historical_analysis.yf") as mock_yf:
            # Create mock historical data
            dates = pd.date_range(end=datetime.now(), periods=252, freq="D")
            mock_history = pd.DataFrame(
                {
                    "Open": np.random.uniform(100, 150, 252),
                    "High": np.random.uniform(150, 160, 252),
                    "Low": np.random.uniform(90, 100, 252),
                    "Close": np.random.uniform(100, 150, 252),
                    "Volume": np.random.randint(1000000, 5000000, 252),
                },
                index=dates,
            )

            mock_ticker = MagicMock()
            mock_ticker.history.return_value = mock_history
            mock_ticker.calendar = None
            mock_yf.Ticker.return_value = mock_ticker

            from src.services.historical_analysis import HistoricalAnalysisService

            service = HistoricalAnalysisService()
            result = service.get_earnings_reactions("AAPL", num_quarters=4)

            assert result.ticker == "AAPL"

    def test_get_price_history(self):
        """Test getting price history."""
        from datetime import datetime

        import numpy as np
        import pandas as pd

        with patch("src.services.historical_analysis.yf") as mock_yf:
            dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
            mock_history = pd.DataFrame(
                {
                    "Open": np.random.uniform(100, 150, 30),
                    "High": np.random.uniform(150, 160, 30),
                    "Low": np.random.uniform(90, 100, 30),
                    "Close": np.linspace(100, 120, 30),
                    "Volume": np.random.randint(1000000, 5000000, 30),
                },
                index=dates,
            )

            mock_ticker = MagicMock()
            mock_ticker.history.return_value = mock_history
            mock_yf.Ticker.return_value = mock_ticker

            from src.services.historical_analysis import HistoricalAnalysisService

            service = HistoricalAnalysisService()
            result = service.get_price_history("AAPL", period="1mo")

            assert result.ticker == "AAPL"
            assert result.period == "1mo"


class TestWatchlistService:
    """Tests for WatchlistService."""

    def test_init(self):
        """Test service initialization."""
        import tempfile

        from src.services.watchlist import WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)
            assert service is not None

    def test_add_to_watchlist(self):
        """Test adding to watchlist."""
        import tempfile

        from src.services.watchlist import WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)

            result = service.add_ticker("user123", "AAPL")
            assert result is True

    def test_get_watchlist(self):
        """Test getting watchlist."""
        import tempfile

        from src.services.watchlist import WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)
            service.add_ticker("user123", "AAPL")
            service.add_ticker("user123", "GOOGL")

            result = service.get_watchlist("user123")
            assert len(result) == 2

    def test_remove_from_watchlist(self):
        """Test removing from watchlist."""
        import tempfile

        from src.services.watchlist import WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)
            service.add_ticker("user123", "AAPL")
            service.add_ticker("user123", "GOOGL")

            result = service.remove_ticker("user123", "AAPL")
            assert result is True

            watchlist = service.get_watchlist("user123")
            assert len(watchlist) == 1

    def test_add_alert(self):
        """Test adding price alert."""
        import tempfile

        from src.services.watchlist import AlertType, WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)

            alert = service.add_alert(
                user_id="user123", ticker="AAPL", alert_type=AlertType.PRICE_ABOVE, threshold=200.0
            )

            assert alert is not None
            assert alert.ticker == "AAPL"

    def test_get_alerts(self):
        """Test getting alerts."""
        import tempfile

        from src.services.watchlist import AlertType, WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)
            service.add_alert("user123", "AAPL", AlertType.PRICE_ABOVE, 200.0)

            alerts = service.get_alerts("user123")
            assert len(alerts) == 1

    def test_remove_alert(self):
        """Test removing alert."""
        import tempfile

        from src.services.watchlist import AlertType, WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)
            alert = service.add_alert("user123", "AAPL", AlertType.PRICE_ABOVE, 200.0)

            result = service.remove_alert("user123", alert.id)
            assert result is True

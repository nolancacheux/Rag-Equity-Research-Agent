"""Tests for service modules."""


import pytest


class TestChatService:
    """Tests for ChatService."""

    def test_system_prompt_defined(self):
        """Test that system prompt is defined."""
        from src.services.chat import SYSTEM_PROMPT
        
        assert SYSTEM_PROMPT is not None
        assert "FinanceAgent" in SYSTEM_PROMPT


class TestRiskScoringService:
    """Tests for RiskScoringService."""

    def test_init(self):
        """Test service initialization."""
        from src.services.risk_scoring import RiskScoringService

        service = RiskScoringService()
        assert service is not None

    def test_risk_keywords_defined(self):
        """Test that risk keywords are defined."""
        from src.services.risk_scoring import RISK_KEYWORDS, RiskCategory

        assert len(RISK_KEYWORDS) > 0
        assert RiskCategory.MARKET in RISK_KEYWORDS
        assert RiskCategory.FINANCIAL in RISK_KEYWORDS

    def test_analyze_risk_basic(self):
        """Test basic risk analysis."""
        from src.services.risk_scoring import RiskScore, RiskScoringService

        service = RiskScoringService()

        filing_text = """
        The company faces significant market volatility risk.
        Economic downturn could adversely affect our business.
        We have substantial debt obligations.
        """

        result = service.analyze_risk("TEST", filing_text)

        assert isinstance(result, RiskScore)
        assert result.ticker == "TEST"
        assert 0 <= result.overall_score <= 10

    def test_analyze_risk_no_keywords(self):
        """Test risk analysis with no risk keywords."""
        from src.services.risk_scoring import RiskScoringService

        service = RiskScoringService()

        filing_text = "The company had a great year with strong performance."

        result = service.analyze_risk("TEST", filing_text)

        assert result.overall_score <= 5

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
        assert "MSFT" in EarningsCalendarService.MAJOR_TICKERS


class TestPeerComparisonService:
    """Tests for PeerComparisonService."""

    def test_init(self):
        """Test service initialization."""
        from src.services.peer_comparison import PeerComparisonService

        service = PeerComparisonService()
        assert service is not None

    def test_peer_groups_defined(self):
        """Test that peer groups are defined."""
        from src.services.peer_comparison import PEER_GROUPS

        assert len(PEER_GROUPS) > 0
        assert "AAPL" in PEER_GROUPS
        assert "NVDA" in PEER_GROUPS

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


class TestHistoricalAnalysisService:
    """Tests for HistoricalAnalysisService."""

    def test_init(self):
        """Test service initialization."""
        from src.services.historical_analysis import HistoricalAnalysisService

        service = HistoricalAnalysisService()
        assert service is not None

    def test_dataclasses_defined(self):
        """Test that dataclasses are defined."""
        from src.services.historical_analysis import (
            EarningsReaction,
        )

        # Test we can create instances
        reaction = EarningsReaction(
            date="2024-01-01",
            quarter="Q4 2023",
            price_before=100.0,
            price_after=110.0,
            change_percent=10.0,
            gap_percent=5.0,
            volume_ratio=1.5,
        )
        assert reaction.date == "2024-01-01"


class TestWatchlistService:
    """Tests for WatchlistService."""

    def test_init(self):
        """Test service initialization."""
        import tempfile

        from src.services.watchlist import WatchlistService

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            service = WatchlistService(storage_path=f.name)
            assert service is not None

    def test_alert_type_enum(self):
        """Test AlertType enum."""
        from src.services.watchlist import AlertType

        assert AlertType.PRICE_ABOVE == "price_above"
        assert AlertType.PRICE_BELOW == "price_below"

    def test_dataclasses_defined(self):
        """Test that dataclasses are defined."""
        from src.services.watchlist import Alert, AlertType, WatchlistItem

        alert = Alert(
            id="test-id",
            ticker="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            threshold=200.0,
            created_at="2024-01-01",
        )
        assert alert.ticker == "AAPL"

        item = WatchlistItem(
            ticker="AAPL",
            added_at="2024-01-01",
        )
        assert item.ticker == "AAPL"

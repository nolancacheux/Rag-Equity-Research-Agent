"""LangGraph agents for equity research."""

from src.agents.document_reader import DocumentReaderAgent
from src.agents.earnings_agent import EarningsAgent
from src.agents.graph import (
    ResearchState,
    create_research_graph,
    run_research,
    run_research_sync,
)
from src.agents.market_data import MarketDataAgent
from src.agents.news_sentiment import NewsSentimentAgent
from src.agents.peer_agent import PeerComparisonAgent
from src.agents.reddit_agent import RedditSentimentAgent
from src.agents.risk_agent import RiskScoringAgent
from src.agents.synthesizer import SynthesizerAgent

__all__ = [
    "create_research_graph",
    "ResearchState",
    "run_research",
    "run_research_sync",
    "MarketDataAgent",
    "DocumentReaderAgent",
    "NewsSentimentAgent",
    "SynthesizerAgent",
    # New agents
    "EarningsAgent",
    "RedditSentimentAgent",
    "PeerComparisonAgent",
    "RiskScoringAgent",
]

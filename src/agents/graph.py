"""LangGraph orchestration for equity research agents.

Enhanced graph with new data sources:
- Earnings call transcripts
- Reddit sentiment analysis
- Peer comparison
- Risk scoring from 10-K
"""

import re
from typing import Any, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from src.agents.document_reader import run_document_reader_node
from src.agents.earnings_agent import run_earnings_agent_node
from src.agents.market_data import run_market_data_node
from src.agents.news_sentiment import run_news_sentiment_node
from src.agents.peer_agent import run_peer_agent_node
from src.agents.reddit_agent import run_reddit_agent_node
from src.agents.risk_agent import run_risk_agent_node
from src.agents.synthesizer import run_synthesizer_node

logger = structlog.get_logger()


class ResearchState(TypedDict, total=False):
    """State for the research graph."""

    # Input
    query: str
    tickers: list[str]
    document_queries: list[str]

    # Feature flags (control which agents run)
    include_earnings: bool
    include_reddit: bool
    include_peers: bool
    include_risk: bool

    # Agent outputs
    market_data: dict[str, Any] | None
    document_analysis: list[dict[str, Any]] | None
    news_analysis: list[dict[str, Any]] | None

    # New agent outputs
    earnings_analysis: list[dict[str, Any]] | None
    reddit_sentiment: list[dict[str, Any]] | None
    peer_analysis: list[dict[str, Any]] | None
    risk_assessment: list[dict[str, Any]] | None

    # Final output
    report: dict[str, Any] | None

    # Errors
    errors: list[str]


def parse_query(state: ResearchState) -> ResearchState:
    """Parse the user query to extract tickers and document queries.

    This node analyzes the query and populates:
    - tickers: Stock symbols mentioned
    - document_queries: Topics to search in SEC filings
    """
    query = state.get("query", "")

    # Extract ticker symbols (uppercase 1-5 letter words)
    ticker_pattern = r"\b([A-Z]{1,5})\b"
    potential_tickers = re.findall(ticker_pattern, query.upper())

    # Filter common words that aren't tickers
    stop_words = {
        "A",
        "I",
        "AND",
        "OR",
        "THE",
        "TO",
        "IN",
        "OF",
        "FOR",
        "ON",
        "AT",
        "IS",
        "IT",
        "AS",
        "BE",
        "BY",
        "AN",
        "IF",
        "VS",
        "PE",
        "CEO",
        "CFO",
        "USA",
        "UK",
        "EU",
        "AI",
        "ML",
        "API",
        "SEC",
        "IPO",
        "ETF",
        "NYSE",
    }

    tickers = [t for t in potential_tickers if t not in stop_words]

    # Use provided tickers if already set, otherwise use parsed
    if not state.get("tickers"):
        state["tickers"] = tickers[:5]  # Limit to 5 tickers

    # Extract document search queries
    doc_query_patterns = [
        r"(?:check|search|find|look for|analyze)\s+(?:in\s+)?(?:their\s+)?(?:10-K|annual report|filing)\s+(?:for\s+)?(.+?)(?:\.|$)",
        r"(?:risks?\s+(?:related\s+to|about|regarding))\s+(.+?)(?:\.|$)",
        r"what\s+(?:are|is)\s+(?:the\s+)?(.+?)(?:\s+risks?)?(?:\.|$)",
    ]

    doc_queries = []
    for pattern in doc_query_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        doc_queries.extend(matches)

    # Add common financial topics if mentioned
    topics = ["China", "supply chain", "regulatory", "competition", "debt", "growth"]
    for topic in topics:
        if topic.lower() in query.lower() and topic not in doc_queries:
            doc_queries.append(topic)

    if not state.get("document_queries"):
        state["document_queries"] = doc_queries[:3]  # Limit to 3 queries

    state["errors"] = state.get("errors", [])

    logger.info(
        "query_parsed",
        query=query[:100],
        tickers=state["tickers"],
        doc_queries=state["document_queries"],
    )

    return state


def should_analyze_documents(state: ResearchState) -> str:
    """Decide if document analysis is needed."""
    # Analyze documents if we have document queries
    if state.get("document_queries"):
        return "document_reader"
    return "parallel_analysis"


def route_after_documents(state: ResearchState) -> str:
    """Route after document analysis."""
    return "parallel_analysis"


async def run_parallel_analysis(state: dict) -> dict:
    """Run earnings, reddit, peers, and risk analysis in parallel.

    This node runs multiple analyses concurrently to speed up the pipeline.
    Only runs analyses that are enabled in state flags.
    """
    import asyncio

    tasks = []
    task_names = []

    # Check which analyses to run (default: all disabled for backwards compat)
    if state.get("include_earnings", False):
        tasks.append(run_earnings_agent_node(state))
        task_names.append("earnings")

    if state.get("include_reddit", False):
        tasks.append(run_reddit_agent_node(state))
        task_names.append("reddit")

    if state.get("include_peers", False):
        tasks.append(run_peer_agent_node(state))
        task_names.append("peers")

    if state.get("include_risk", False):
        tasks.append(run_risk_agent_node(state))
        task_names.append("risk")

    if not tasks:
        # No parallel tasks, just continue
        return {
            "earnings_analysis": None,
            "reddit_sentiment": None,
            "peer_analysis": None,
            "risk_assessment": None,
        }

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge results
    merged = {
        "earnings_analysis": None,
        "reddit_sentiment": None,
        "peer_analysis": None,
        "risk_assessment": None,
        "errors": state.get("errors", []),
    }

    for name, result in zip(task_names, results, strict=False):
        if isinstance(result, Exception):
            merged["errors"].append(f"{name} analysis failed: {result}")
            continue

        if name == "earnings":
            merged["earnings_analysis"] = result.get("earnings_analysis")
        elif name == "reddit":
            merged["reddit_sentiment"] = result.get("reddit_sentiment")
        elif name == "peers":
            merged["peer_analysis"] = result.get("peer_analysis")
        elif name == "risk":
            merged["risk_assessment"] = result.get("risk_assessment")

        merged["errors"].extend(result.get("errors", []))

    logger.info("parallel_analysis_complete", analyses=task_names)
    return merged


def create_research_graph() -> StateGraph:
    """Create the LangGraph research workflow.

    Graph structure (enhanced):

    [parse_query] -> [market_data] -> [document_reader?] -> [parallel_analysis] -> [news_sentiment] -> [synthesizer] -> END
                                                                    |
                                                    (earnings, reddit, peers, risk)

    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("parse_query", parse_query)
    workflow.add_node("market_data", run_market_data_node)
    workflow.add_node("document_reader", run_document_reader_node)
    workflow.add_node("parallel_analysis", run_parallel_analysis)
    workflow.add_node("news_sentiment", run_news_sentiment_node)
    workflow.add_node("synthesizer", run_synthesizer_node)

    # Define edges
    workflow.set_entry_point("parse_query")
    workflow.add_edge("parse_query", "market_data")

    # Conditional edge: analyze documents only if queries exist
    workflow.add_conditional_edges(
        "market_data",
        should_analyze_documents,
        {
            "document_reader": "document_reader",
            "parallel_analysis": "parallel_analysis",
        },
    )

    workflow.add_edge("document_reader", "parallel_analysis")
    workflow.add_edge("parallel_analysis", "news_sentiment")
    workflow.add_edge("news_sentiment", "synthesizer")
    workflow.add_edge("synthesizer", END)

    # Compile
    graph = workflow.compile()
    logger.info("research_graph_created")

    return graph


async def run_research(
    query: str,
    tickers: list[str] | None = None,
    include_earnings: bool = False,
    include_reddit: bool = False,
    include_peers: bool = False,
    include_risk: bool = False,
) -> dict[str, Any]:
    """Run the research workflow.

    Args:
        query: Research query
        tickers: Optional list of tickers (auto-detected if not provided)
        include_earnings: Include earnings call analysis
        include_reddit: Include Reddit sentiment analysis
        include_peers: Include peer comparison analysis
        include_risk: Include 10-K risk scoring

    Returns:
        Research results including report
    """
    graph = create_research_graph()

    initial_state: ResearchState = {
        "query": query,
        "tickers": tickers or [],
        "document_queries": [],
        "include_earnings": include_earnings,
        "include_reddit": include_reddit,
        "include_peers": include_peers,
        "include_risk": include_risk,
        "errors": [],
    }

    # Run the graph
    result = await graph.ainvoke(initial_state)

    logger.info(
        "research_completed",
        tickers=result.get("tickers"),
        has_report=result.get("report") is not None,
        error_count=len(result.get("errors", [])),
        features={
            "earnings": include_earnings,
            "reddit": include_reddit,
            "peers": include_peers,
            "risk": include_risk,
        },
    )

    return result


def run_research_sync(
    query: str,
    tickers: list[str] | None = None,
    include_earnings: bool = False,
    include_reddit: bool = False,
    include_peers: bool = False,
    include_risk: bool = False,
) -> dict[str, Any]:
    """Synchronous version of run_research.

    Args:
        query: Research query
        tickers: Optional list of tickers
        include_earnings: Include earnings call analysis
        include_reddit: Include Reddit sentiment analysis
        include_peers: Include peer comparison analysis
        include_risk: Include 10-K risk scoring

    Returns:
        Research results
    """
    graph = create_research_graph()

    initial_state: ResearchState = {
        "query": query,
        "tickers": tickers or [],
        "document_queries": [],
        "include_earnings": include_earnings,
        "include_reddit": include_reddit,
        "include_peers": include_peers,
        "include_risk": include_risk,
        "errors": [],
    }

    result = graph.invoke(initial_state)
    return result

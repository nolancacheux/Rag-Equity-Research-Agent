# LangGraph Orchestration

## Overview

LangGraph orchestrates the multi-agent research workflow, coordinating parallel data collection and synthesis.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         parse_query                              │
│              (extract tickers, document queries)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         market_data                              │
│                    (Yahoo Finance quotes)                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐       ┌───────────────────────────────┐
│     document_reader     │       │      parallel_analysis        │
│  (SEC 10-K + hybrid RAG)│       │   (if no doc queries)         │
└─────────────┬───────────┘       └───────────────┬───────────────┘
              │                                   │
              └───────────────┬───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      parallel_analysis                           │
│         (earnings, reddit, peers, risk - concurrent)             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       news_sentiment                             │
│                    (DuckDuckGo news)                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        synthesizer                               │
│               (LLM report generation)                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
                            END
```

## State Definition

```python
class ResearchState(TypedDict, total=False):
    # Input
    query: str
    tickers: list[str]
    document_queries: list[str]
    
    # Feature flags
    include_earnings: bool
    include_reddit: bool
    include_peers: bool
    include_risk: bool

    # Agent outputs
    market_data: dict[str, Any] | None
    document_analysis: list[dict[str, Any]] | None
    news_analysis: list[dict[str, Any]] | None
    earnings_analysis: list[dict[str, Any]] | None
    reddit_sentiment: list[dict[str, Any]] | None
    peer_analysis: list[dict[str, Any]] | None
    risk_assessment: list[dict[str, Any]] | None

    # Final output
    report: dict[str, Any] | None
    errors: list[str]
```

## Agents

### parse_query
Extracts tickers and document search queries from natural language.

```python
# Input: "Analyze NVDA and check for China risks"
# Output: tickers=["NVDA"], document_queries=["China risks"]
```

### market_data
Fetches real-time data from Yahoo Finance.

**Data collected:**
- Current price, change %
- P/E ratio, market cap
- Volume, 52-week range
- Key financials

### document_reader
Downloads and searches SEC 10-K filings using hybrid RAG.

**Features:**
- Hybrid search (BM25 + dense embeddings)
- RRF fusion for ranking
- Keyword reranking for relevance
- Auto-download if not indexed

### parallel_analysis
Runs multiple analyses concurrently using `asyncio.gather()`.

**Agents run in parallel:**
- `earnings_agent` - Earnings call transcripts
- `reddit_agent` - Reddit sentiment
- `peer_agent` - Peer comparison
- `risk_agent` - 10-K risk scoring

Each agent only runs if its feature flag is enabled.

### news_sentiment
Searches recent financial news via DuckDuckGo.

### synthesizer
Generates final report using LLM (Groq/OpenAI).

**Combines:**
- Market data summary
- SEC filing analysis
- Earnings call insights
- Reddit sentiment
- Peer comparison
- Risk assessment
- News sentiment

## Graph Creation

```python
def create_research_graph() -> StateGraph:
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
    
    # Conditional: document_reader or skip to parallel
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

    return workflow.compile()
```

## Usage

```python
from src.agents import run_research

# Basic analysis
result = await run_research(
    query="Analyze NVIDIA",
    tickers=["NVDA"]
)

# Full analysis with all features
result = await run_research(
    query="Analyze NVIDIA",
    tickers=["NVDA"],
    include_earnings=True,
    include_reddit=True,
    include_peers=True,
    include_risk=True,
)

# Access results
print(result["report"]["full_report"])
print(result["market_data"])
print(result["earnings_analysis"])
print(result["reddit_sentiment"])
```

## Performance

With parallel analysis enabled:
- **Sequential time**: ~60-90 seconds
- **With parallel**: ~30-45 seconds

The `parallel_analysis` node uses `asyncio.gather()` to run all enabled analyses concurrently.

## Error Handling

Each agent catches and logs errors without crashing the pipeline:

```python
try:
    result = await agent.analyze(ticker)
except Exception as e:
    logger.error("analysis_failed", error=str(e))
    return {"errors": [str(e)]}
```

Errors are collected in `state["errors"]` and included in the final report.

## Adding New Agents

1. Create agent in `src/agents/my_agent.py`:
```python
async def run_my_agent_node(state: dict) -> dict:
    # ... analysis logic
    return {"my_output": result, "errors": []}
```

2. Add to `parallel_analysis` in `graph.py`:
```python
if state.get("include_my_feature", False):
    tasks.append(run_my_agent_node(state))
    task_names.append("my_feature")
```

3. Update `ResearchState` with new fields

4. Update `synthesizer.py` to include new data

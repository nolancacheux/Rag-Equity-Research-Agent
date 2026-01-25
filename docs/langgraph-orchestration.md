# LangGraph Orchestration

## Why LangGraph?

LangGraph orchestrates the different financial research agents in a structured and deterministic workflow.

### Advantages over Classic LangChain

| Criteria | LangGraph | LangChain Agents |
|----------|-----------|------------------|
| **Flow Control** | Explicit (graph) | Implicit (LLM decides) |
| **Determinism** | High | Variable |
| **Debugging** | Easy (visualization) | Difficult |
| **Shared State** | Native (TypedDict) | Manual |
| **LLM Costs** | Predictable | Unpredictable |

### Reasons for Choice

1. **Structured financial workflow**: The order of analyses matters (data → docs → news → synthesis)
2. **Typed state**: TypedDict ensures data consistency between agents
3. **Debugging**: Clear flow visualization to identify errors
4. **Controlled costs**: No infinite loops possible

## Graph Architecture

```
[parse_query] → [market_data] → [document_reader?] → [news_sentiment] → [synthesizer] → END
                                       ↓
                              (skip if no doc queries)
```

### Nodes

| Node | Responsibility | Input | Output |
|------|----------------|-------|--------|
| `parse_query` | Extract tickers + queries | `query` | `tickers`, `document_queries` |
| `market_data` | Prices, fundamentals via yfinance | `tickers` | `market_data` |
| `document_reader` | RAG on SEC filings | `tickers`, `document_queries` | `document_analysis` |
| `news_sentiment` | News sentiment analysis | `tickers` | `news_analysis` |
| `synthesizer` | Final LLM report | All outputs | `report` |

## Graph State (ResearchState)

```python
class ResearchState(TypedDict, total=False):
    # Input
    query: str
    tickers: list[str]
    document_queries: list[str]
    
    # Agent outputs
    market_data: dict[str, Any] | None
    document_analysis: list[dict[str, Any]] | None
    news_analysis: list[dict[str, Any]] | None
    
    # Final output
    report: dict[str, Any] | None
    
    # Errors
    errors: list[str]
```

## Usage

### Async Research

```python
from src.agents.graph import run_research

result = await run_research(
    query="Analyze NVDA and check their 10-K for China risks",
    tickers=["NVDA"]  # Optional, auto-detected otherwise
)

print(result["report"])
```

### Sync Research

```python
from src.agents.graph import run_research_sync

result = run_research_sync("Compare AAPL and MSFT revenue growth")
```

## Conditional Edges

The graph includes conditional logic:

```python
def should_analyze_documents(state: ResearchState) -> str:
    """Skip document analysis if no document queries."""
    if state.get("document_queries"):
        return "document_reader"
    return "news_sentiment"  # Skip directly to news
```

## Tracing with LangSmith

Enabled via environment variables:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_xxx
LANGCHAIN_PROJECT=equity-research-agent
```

Allows visualization of:
- Execution time per node
- Tokens consumed
- Errors and retries

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith](https://smith.langchain.com/)

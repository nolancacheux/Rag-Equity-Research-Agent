# Financial Data Tools

## Overview

The project uses multiple financial data sources:

```
src/tools/
├── yfinance_tool.py    # Prices, fundamentals, history
├── sec_edgar_tool.py   # SEC filings (10-K, 10-Q, 8-K)
└── search_tool.py      # DuckDuckGo for news
```

## yfinance

### Why yfinance?

- **Free**: No API key required
- **Complete**: Prices, fundamentals, dividends, institutional holdings
- **Reliable**: Yahoo Finance data

### Available Data

| Type | Method | Cache TTL |
|------|--------|-----------|
| Real-time price | `get_price()` | 5 min |
| History | `get_history()` | 1h |
| Fundamentals | `get_fundamentals()` | 1h |
| Company info | `get_info()` | 24h |

### Usage

```python
from src.tools.yfinance_tool import YFinanceTool

tool = YFinanceTool()

# Current price
price = tool.get_price("NVDA")
# {"symbol": "NVDA", "price": 875.50, "change": 2.3, "volume": 45000000}

# Fundamentals
fundamentals = tool.get_fundamentals("NVDA")
# {"pe_ratio": 65.2, "market_cap": 2150000000000, "revenue": 60922000000, ...}

# History
history = tool.get_history("NVDA", period="1mo")
# DataFrame with Open, High, Low, Close, Volume
```

## SEC EDGAR

### Why SEC EDGAR?

- **Official**: Primary source for US filings
- **Complete**: 10-K, 10-Q, 8-K, proxy statements
- **Free**: Public API

### Configuration

```env
SEC_USER_AGENT=EquityResearchAgent your-email@example.com
```

> **Important**: SEC requires a valid User-Agent with contact email.

### Supported Filings

| Type | Description | Frequency |
|------|-------------|-----------|
| 10-K | Annual report | Yearly |
| 10-Q | Quarterly report | Quarterly |
| 8-K | Major events | Ad-hoc |

### Usage

```python
from src.tools.sec_edgar_tool import SECEdgarTool

tool = SECEdgarTool()

# Download latest 10-K
filing = tool.download_filing("NVDA", "10-K")

# List recent filings
filings = tool.list_filings("NVDA", form_type="10-K", count=5)
```

## DuckDuckGo Search

### Why DuckDuckGo?

- **Free**: No API key required
- **No tracking**: Privacy-respecting
- **News**: Recent news search

### Usage

```python
from src.tools.search_tool import SearchTool

tool = SearchTool()

# General web search
results = tool.search("NVIDIA earnings Q4 2024")

# News search
news = tool.search_news("NVDA stock", max_results=10)
```

## Rate Limiting

All external sources have rate limiting:

| Source | Limit | Implementation |
|--------|-------|----------------|
| yfinance | 2000/h | Built-in |
| SEC EDGAR | 10/sec | `tenacity` retry |
| DuckDuckGo | 20/min | `slowapi` |

### Example with tenacity

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10)
)
def fetch_with_retry():
    ...
```

## Resources

- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [SEC EDGAR](https://www.sec.gov/developer)
- [DuckDuckGo Search](https://github.com/deedy5/duckduckgo_search)

# claude.md - Agent Instructions

## Project Overview

**Equity Research Agent** - AI-powered financial analysis using LangGraph, RAG, and real-time market data. Features DCF valuation, risk scoring, peer comparison, Reddit sentiment, earnings calendar, and more.

- **Tech**: LangGraph + FastAPI + Telegram Bot
- **Data**: All free (Yahoo Finance, SEC EDGAR, Reddit, DuckDuckGo)
- **LLM**: Groq free tier (Llama 3.3 70B) or Azure OpenAI / OpenAI

## Architecture

```
src/
├── agents/              # LangGraph agents
│   ├── graph.py             # Main orchestration (parallel analysis)
│   ├── market_data.py       # Yahoo Finance data
│   ├── document_reader.py   # SEC filing RAG + hybrid search + reranking
│   ├── news_sentiment.py    # News analysis
│   ├── earnings_agent.py    # Earnings call transcripts
│   ├── reddit_agent.py      # Reddit sentiment (WSB, stocks)
│   ├── peer_agent.py        # Peer comparison
│   ├── risk_agent.py        # 10-K risk scoring
│   └── synthesizer.py       # Report generation
├── services/            # Business logic
│   ├── watchlist.py         # Watchlist & alerts
│   ├── dcf_valuation.py     # DCF fair value calculator
│   ├── earnings_calendar.py # Earnings dates tracker
│   ├── historical_analysis.py # Price/earnings history
│   ├── peer_comparison.py   # Peer metrics comparison
│   └── risk_scoring.py      # 10-K risk factor analysis
├── tools/               # Data fetchers
│   ├── yfinance_tool.py     # Market data
│   ├── sec_edgar_tool.py    # SEC filings
│   ├── search_tool.py       # DuckDuckGo news
│   ├── earnings_call_tool.py # Earnings transcripts
│   └── reddit_sentiment_tool.py # Reddit API
├── rag/                 # RAG pipeline
│   ├── hybrid_search.py     # BM25 + dense + RRF fusion
│   ├── reranker.py          # Keyword + LLM reranking
│   ├── vector_store.py      # Qdrant integration
│   ├── embeddings.py        # Azure OpenAI embeddings
│   └── chunking.py          # Document chunking
├── api/                 # FastAPI endpoints
│   ├── main.py              # All REST endpoints
│   ├── metrics.py           # Prometheus metrics
│   └── middleware/auth.py   # API key authentication
├── telegram/            # Telegram bot
│   ├── bot.py               # Bot setup & command registration
│   ├── handlers.py          # Core command handlers
│   ├── handlers_v2.py       # New feature handlers (DCF, Risk, etc.)
│   ├── keyboards.py         # Inline button menus
│   ├── i18n.py              # Translations (EN/FR)
│   ├── client.py            # API client
│   └── formatters.py        # Message formatting
├── config/              # Settings
│   └── settings.py          # Pydantic settings
└── utils/               # Utilities
    └── cache.py             # Redis caching

terraform/               # Azure IaC
tests/                   # Unit tests (98% coverage)
docs/                    # Documentation
```

## Features Summary

| Category | Features |
|----------|----------|
| **Core** | Analyze, Quote, Compare |
| **Tools** | DCF Valuation, Risk Score, Peer Comparison, Reddit Sentiment, Earnings Calendar, Historical Analysis |
| **Watchlist** | Track stocks, Price alerts, P/E alerts |
| **RAG** | Hybrid search (BM25+dense), Reranking, Multi-source |

## API Endpoints

### Core
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/metrics` | GET | No | Prometheus metrics |
| `/analyze` | POST | Yes | Full research analysis |
| `/quote/{ticker}` | GET | Yes | Stock quote |
| `/compare/{tickers}` | GET | Yes | Compare stocks |

### Advanced Tools
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dcf/{ticker}` | GET | DCF fair value |
| `/risk/{ticker}` | GET | Risk score (1-10) |
| `/peers/{ticker}` | GET | Peer comparison |
| `/reddit/{ticker}` | GET | Reddit sentiment |
| `/earnings/{ticker}` | GET | Earnings call analysis |
| `/calendar` | GET | Earnings calendar |
| `/history/{ticker}` | GET | Historical analysis |

### Watchlist
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/watchlist/{user_id}` | GET | Get watchlist |
| `/watchlist/{user_id}/add` | POST | Add to watchlist |
| `/watchlist/{user_id}/alert` | POST | Create alert |

## Telegram Commands

### Core
| Command | Alias | Description |
|---------|-------|-------------|
| `/start` | - | Welcome & language |
| `/menu` | - | Main menu |
| `/help` | - | Feature overview |
| `/analyze` | `/a` | Deep analysis |
| `/quote` | `/q` | Stock quote |
| `/compare` | `/c` | Compare stocks |

### Tools
| Command | Alias | Description |
|---------|-------|-------------|
| `/dcf` | `/valuation` | DCF fair value |
| `/risk` | - | Risk score |
| `/peers` | - | Peer comparison |
| `/reddit` | `/wsb` | Reddit sentiment |
| `/calendar` | `/earnings` | Earnings calendar |
| `/history` | `/hist` | Historical analysis |

### Watchlist
| Command | Description |
|---------|-------------|
| `/watchlist` | View watchlist |
| `/watchlist add NVDA` | Add stock |
| `/alert NVDA above 150` | Price alert |

## Environment Variables

### LLM (at least one required)
```bash
# Option 1: Groq (FREE - recommended)
GROQ_API_KEY=gsk_...

# Option 2: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Option 3: OpenAI
OPENAI_API_KEY=sk-...
```

### Infrastructure
```bash
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
SEC_USER_AGENT=YourApp your-email@example.com
```

### Security
```bash
API_SECRET_KEY=your-secret-key  # openssl rand -hex 32
```

### Telegram
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
API_BASE_URL=http://localhost:8000
```

## Development

```bash
# Install
pip install -e ".[dev]"

# Test
pytest --cov=src --cov-report=term-missing

# Lint
ruff check src/ --fix && ruff format src/

# Run API
uvicorn src.api.main:app --reload

# Run Telegram bot
python -m src.telegram.bot

# Docker
docker compose up -d
```

## Code Standards

- **Typing**: Full type hints, mypy strict
- **Formatting**: Ruff (100 char lines)
- **Testing**: pytest, 98% coverage minimum
- **Commits**: Conventional commits
- **Security**: No hardcoded secrets

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/agents/graph.py` | LangGraph orchestration, parallel analysis |
| `src/api/main.py` | All API endpoints |
| `src/telegram/bot.py` | Bot setup, command registration |
| `src/telegram/keyboards.py` | All inline button menus |
| `src/telegram/i18n.py` | All UI text (EN/FR) |
| `src/services/*.py` | Business logic for each feature |

## Adding New Features

1. **Service**: Create `src/services/my_feature.py`
2. **Agent** (optional): Create `src/agents/my_agent.py`
3. **API**: Add endpoint in `src/api/main.py`
4. **Telegram**: Add handler in `src/telegram/handlers_v2.py`
5. **Keyboard**: Add button in `src/telegram/keyboards.py`
6. **i18n**: Add translations in `src/telegram/i18n.py`
7. **Docs**: Update `docs/features.md` and `README.md`
8. **Tests**: Add tests in `tests/`

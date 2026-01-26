# Real-Time Equity Research Agent

AI-powered financial analysis agent that acts as an autonomous Quantitative Analyst, scanning real market data, SEC filings, earnings calls, and social sentiment to generate professional equity research reports.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## What It Does

Ask a question like:

> "Analyze NVIDIA's current situation. Compare their P/E Ratio with AMD, and check their latest 10-K report for China-related risks."

The agent will:
1. **Fetch real-time market data** via Yahoo Finance
2. **Download and analyze SEC 10-K reports** using hybrid RAG
3. **Analyze earnings call transcripts** for guidance and sentiment
4. **Check Reddit sentiment** from WSB, stocks, investing
5. **Compare with industry peers** automatically
6. **Score risk factors** from 10-K (1-10 scale)
7. **Calculate fair value** using DCF model
8. **Synthesize everything** into a professional research report

## Features

### Core Analysis
| Feature | Description |
|---------|-------------|
| **📊 Deep Analysis** | Multi-source research with SEC filings, news, earnings calls |
| **💹 Real-time Quotes** | Live prices, P/E, market cap, volume |
| **📈 Stock Comparison** | Side-by-side metrics comparison |

### Advanced Tools
| Tool | Command | Description |
|------|---------|-------------|
| **💰 DCF Valuation** | `/dcf NVDA` | Calculate fair value using discounted cash flow |
| **⚠️ Risk Score** | `/risk NVDA` | 10-K risk analysis with score 1-10 |
| **👥 Peer Comparison** | `/peers NVDA` | Compare vs industry competitors |
| **🔴 Reddit Sentiment** | `/reddit NVDA` | WSB/stocks/investing sentiment |
| **📅 Earnings Calendar** | `/calendar` | Upcoming earnings dates |
| **📜 Historical Analysis** | `/history NVDA` | Price history & earnings reactions |

### Watchlist & Alerts
| Feature | Command | Description |
|---------|---------|-------------|
| **📋 Watchlist** | `/watchlist` | Track your favorite stocks |
| **➕ Add Stock** | `/watchlist add NVDA` | Add to watchlist |
| **🔔 Price Alert** | `/alert NVDA above 150` | Get notified when price crosses threshold |
| **📊 P/E Alert** | `/alert AAPL pe_above 30` | Alert on valuation metrics |

### Data Sources (All Free)
| Source | Description |
|--------|-------------|
| **Yahoo Finance** | Real-time prices, financials, ratios, history |
| **SEC EDGAR** | 10-K annual reports with RAG search |
| **Earnings Calls** | Transcripts from Motley Fool + aggregators |
| **Reddit** | r/wallstreetbets, r/stocks, r/investing |
| **DuckDuckGo** | Real-time financial news |

### Advanced RAG
| Feature | Description |
|---------|-------------|
| **Hybrid Search** | BM25 sparse + dense embeddings with RRF fusion |
| **Reranking** | Keyword boost + optional LLM reranking |
| **Multi-source** | Query across SEC filings, earnings calls, news |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Market Data  │   │   Multi-RAG   │   │   Parallel    │
│    Agent      │   │    Router     │   │   Analysis    │
└───────────────┘   └───────┬───────┘   └───────┬───────┘
                            │                   │
        ┌───────────────────┼───────┐   ┌───────┼───────┐
        ▼                   ▼       ▼   ▼       ▼       ▼
┌─────────────┐     ┌─────────────┐   ┌─────────────┐
│ SEC Filings │     │  Earnings   │   │   Reddit    │
│   + RAG     │     │    Calls    │   │  Sentiment  │
└─────────────┘     └─────────────┘   └─────────────┘
        │                   │               │
        └───────────────────┼───────────────┘
                            ▼
                    ┌───────────────┐
                    │  Synthesizer  │
                    │    Agent      │
                    └───────────────┘
```

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/nolancacheux/equity-research-agent.git
cd equity-research-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required:
- `GROQ_API_KEY` - Free at [console.groq.com](https://console.groq.com) (recommended)
- OR `AZURE_OPENAI_*` / `OPENAI_API_KEY`

Optional:
- `QDRANT_URL` - Vector database (default: localhost:6333)
- `REDIS_URL` - Cache (default: localhost:6379)
- `LANGCHAIN_API_KEY` - LangSmith monitoring

### 3. Run with Docker

```bash
docker-compose up -d
```

### 4. Or Run Locally

```bash
# Start dependencies
docker-compose up -d qdrant redis

# Run API
uvicorn src.api.main:app --reload

# Run Telegram bot (separate terminal)
python -m src.telegram.bot
```

## API Endpoints

### Core
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/quote/{ticker}` | GET | Stock quote |
| `/compare/{tickers}` | GET | Compare stocks |
| `/analyze` | POST | Full research analysis |

### Advanced Tools
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dcf/{ticker}` | GET | DCF fair value |
| `/risk/{ticker}` | GET | Risk score from 10-K |
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

## Telegram Bot Commands

### Core Commands
- `/start` - Welcome & language selection
- `/menu` - Main menu with buttons
- `/help` - Feature overview
- `/analyze <query>` - Deep analysis
- `/quote <ticker>` or `/q` - Quick quote
- `/compare <tickers>` or `/c` - Compare stocks

### Tool Commands
- `/dcf <ticker>` - DCF valuation
- `/risk <ticker>` - Risk score
- `/peers <ticker>` - Peer comparison
- `/reddit <ticker>` or `/wsb` - Reddit sentiment
- `/calendar` or `/earnings` - Earnings calendar
- `/history <ticker>` - Price history
- `/history <ticker> earnings` - Earnings reactions

### Watchlist Commands
- `/watchlist` or `/wl` - View watchlist
- `/watchlist add <ticker>` - Add stock
- `/watchlist remove <ticker>` - Remove stock
- `/alert <ticker> above <price>` - Price alert
- `/alert <ticker> below <price>` - Price alert
- `/alert <ticker> pe_above <value>` - P/E alert

## Tech Stack

| Category | Technologies |
|----------|--------------|
| **LLM** | Groq (free), Azure OpenAI, OpenAI |
| **Orchestration** | LangGraph, LangChain |
| **Data** | yfinance, SEC EDGAR, Reddit API |
| **RAG** | Qdrant, Hybrid Search (BM25 + dense) |
| **API** | FastAPI, Pydantic |
| **Bot** | python-telegram-bot |
| **Cache** | Redis |
| **Infra** | Docker, Azure Container Apps |
| **CI/CD** | GitHub Actions |

## Project Structure

```
src/
├── agents/              # LangGraph agents
│   ├── graph.py         # Main orchestration
│   ├── market_data.py   # Yahoo Finance agent
│   ├── document_reader.py # SEC RAG agent
│   ├── news_sentiment.py # News agent
│   ├── earnings_agent.py # Earnings calls
│   ├── reddit_agent.py  # Reddit sentiment
│   ├── peer_agent.py    # Peer comparison
│   ├── risk_agent.py    # Risk scoring
│   └── synthesizer.py   # Report generation
├── services/            # Business logic
│   ├── watchlist.py     # Watchlist & alerts
│   ├── dcf_valuation.py # DCF calculator
│   ├── earnings_calendar.py # Calendar
│   ├── historical_analysis.py # History
│   ├── peer_comparison.py # Peers
│   └── risk_scoring.py  # Risk scoring
├── tools/               # Data fetchers
│   ├── yfinance_tool.py
│   ├── sec_edgar_tool.py
│   ├── earnings_call_tool.py
│   └── reddit_sentiment_tool.py
├── rag/                 # RAG components
│   ├── hybrid_search.py # BM25 + dense
│   ├── reranker.py      # Result reranking
│   ├── vector_store.py  # Qdrant
│   └── embeddings.py
├── api/                 # FastAPI backend
│   └── main.py
└── telegram/            # Telegram bot
    ├── bot.py
    ├── handlers.py
    ├── handlers_v2.py   # New features
    ├── keyboards.py     # Inline buttons
    └── i18n.py          # Translations
```

## Cost

**$0/month** with:
- Groq free tier (Llama 3.3 70B)
- Local Qdrant (or free cloud tier)
- Local Redis
- Yahoo Finance (free)
- SEC EDGAR (free)
- Reddit public API (free)

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

PRs welcome! Please:
1. Follow existing code style (ruff)
2. Add tests for new features
3. Update documentation

# Documentation

Technical documentation for the Equity Research Agent.

## Guides

| Document | Description |
|----------|-------------|
| [Features Overview](features.md) | Complete guide to all features |
| [Telegram Bot](telegram-bot.md) | Bot setup, commands, customization |
| [FastAPI Backend](fastapi-backend.md) | API endpoints and authentication |
| [LangGraph Orchestration](langgraph-orchestration.md) | Agent workflow architecture |
| [Embeddings & RAG](embeddings-rag.md) | Hybrid search, reranking |
| [Qdrant Vector Database](qdrant-vector-database.md) | Vector store setup |
| [Financial Data Tools](financial-data-tools.md) | yfinance, SEC EDGAR |
| [Redis Caching](redis-caching.md) | Cache configuration |
| [Docker Setup](docker-setup.md) | Local development with Docker |
| [Azure Deployment](azure-deployment.md) | Production deployment |
| [CI/CD Setup](ci-cd-setup.md) | GitHub Actions pipelines |

## Quick Links

### Features
- [DCF Valuation](features.md#-dcf-valuation-dcf)
- [Risk Score](features.md#️-risk-score-risk)
- [Peer Comparison](features.md#-peer-comparison-peers)
- [Reddit Sentiment](features.md#-reddit-sentiment-reddit-wsb)
- [Earnings Calendar](features.md#-earnings-calendar-calendar-earnings)
- [Historical Analysis](features.md#-historical-analysis-history-hist)
- [Watchlist & Alerts](features.md#watchlist--alerts)

### API
- [Core Endpoints](fastapi-backend.md#core-endpoints)
- [Tool Endpoints](fastapi-backend.md#tool-endpoints)
- [Authentication](fastapi-backend.md#authentication)

### Telegram
- [Commands](telegram-bot.md#commands)
- [Inline Buttons](telegram-bot.md#inline-buttons)
- [Customization](telegram-bot.md#customization)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Telegram Bot                             │
│           (commands, inline buttons, EN/FR)                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                         FastAPI                                  │
│     (REST endpoints, auth, rate limiting, Prometheus)            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    LangGraph Orchestrator                        │
│              (parallel agents, state management)                 │
└───────┬───────────┬───────────┬───────────┬───────────┬─────────┘
        │           │           │           │           │
   ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
   │ Market  │ │   RAG   │ │ Reddit  │ │  Peers  │ │  Risk   │
   │  Data   │ │ (SEC,   │ │Sentiment│ │ Compare │ │ Scoring │
   │         │ │earnings)│ │         │ │         │ │         │
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │           │           │
   ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
   │ yfinance│ │ Qdrant  │ │ Reddit  │ │ yfinance│ │SEC EDGAR│
   │         │ │ + BM25  │ │   API   │ │         │ │         │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Data Sources

| Source | Data | Cost |
|--------|------|------|
| Yahoo Finance | Prices, financials, history | Free |
| SEC EDGAR | 10-K annual reports | Free |
| Reddit | WSB, stocks, investing posts | Free |
| DuckDuckGo | Financial news | Free |
| Earnings transcripts | Motley Fool, aggregators | Free |

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Groq (free) / Azure OpenAI / OpenAI |
| Orchestration | LangGraph |
| Vector DB | Qdrant |
| Search | Hybrid (BM25 + dense + RRF) |
| API | FastAPI |
| Bot | python-telegram-bot |
| Cache | Redis |
| Infra | Docker, Azure Container Apps |
| CI/CD | GitHub Actions |

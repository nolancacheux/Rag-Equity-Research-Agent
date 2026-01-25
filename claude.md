# claude.md - Agent Instructions

## Project Overview

**Equity Research Agent** - AI-powered financial analysis using LangGraph, RAG, and real-time market data.

## Architecture

```
src/
├── agents/           # LangGraph agents
│   ├── graph.py      # Main orchestration graph
│   ├── market_data.py    # yfinance integration
│   ├── document_reader.py # SEC filing RAG
│   ├── news_sentiment.py  # News analysis
│   └── synthesizer.py     # Report generation
├── api/              # FastAPI endpoints
│   └── main.py       # REST API
├── config/           # Pydantic settings
│   └── settings.py   # Environment config
├── rag/              # RAG pipeline
│   ├── embeddings.py # Sentence transformers
│   ├── chunking.py   # Document chunking
│   └── vector_store.py # Qdrant integration
├── tools/            # Data sources
│   ├── yfinance_tool.py  # Market data
│   ├── sec_edgar_tool.py # SEC filings
│   └── search_tool.py    # DuckDuckGo
└── utils/            # Utilities
    ├── cache.py      # Redis caching
    └── rate_limiter.py # Rate limiting
```

## Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | LangGraph | Agent workflow |
| Embeddings | sentence-transformers (MiniLM) | Local embeddings |
| Vector DB | Qdrant | Semantic search |
| Cache | Redis | API response caching |
| API | FastAPI | REST endpoints |
| Data | yfinance, SEC EDGAR | Financial data |

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=src

# Lint
ruff check src/

# Type check
mypy src/

# Run API locally
uvicorn src.api.main:app --reload

# Docker
docker compose up -d
```

## Environment Variables

Required:
- `OPENAI_API_KEY` - For LLM synthesis

Optional:
- `LANGCHAIN_API_KEY` - LangSmith tracing
- `QDRANT_API_KEY` - If using Qdrant Cloud
- `COMPANIES_HOUSE_API_KEY` - UK company data

## Code Standards

- **Typing**: Full type hints with mypy strict mode
- **Formatting**: Ruff (line length 100)
- **Testing**: pytest with 80%+ coverage target
- **Commits**: Conventional commits (feat/fix/docs/test/chore)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/research` | POST | Start research analysis |
| `/research/{id}` | GET | Get research results |

## Notes

- SEC EDGAR requires valid User-Agent with contact email
- yfinance has rate limits (~2000 req/hour)
- Qdrant runs on port 6333 (REST) and 6334 (gRPC)
- Redis on port 6379

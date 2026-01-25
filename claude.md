# claude.md - Agent Instructions

## Project Overview

**Equity Research Agent** - AI-powered financial analysis using LangGraph, RAG, and real-time market data.

Supports multiple LLM providers: Groq (free), Azure OpenAI, OpenAI.

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
│   ├── embeddings.py # Azure OpenAI embeddings
│   ├── chunking.py   # Document chunking
│   └── vector_store.py # Qdrant integration
├── tools/            # Data sources
│   ├── yfinance_tool.py  # Market data
│   ├── sec_edgar_tool.py # SEC filings
│   └── search_tool.py    # DuckDuckGo
└── utils/            # Utilities
    ├── cache.py      # Redis caching
    └── rate_limiter.py # Rate limiting

tests/                # Unit tests (98% coverage)
```

## Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | LangGraph | Agent workflow |
| LLM | Groq / Azure OpenAI / OpenAI | Analysis and synthesis |
| Embeddings | Azure OpenAI (ada-002) | 1536-dim vectors |
| Vector DB | Qdrant | Semantic search |
| API | FastAPI | REST endpoints |
| Data | yfinance, SEC EDGAR | Financial data |
| Cache | Redis | Response caching |

## LLM Configuration

Priority order (first available is used):
1. **Groq** (free tier) - `GROQ_API_KEY`
2. **Azure OpenAI** - `AZURE_OPENAI_*`
3. **OpenAI** - `OPENAI_API_KEY`

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Lint
ruff check src/

# Type check
mypy src/

# Run API locally
uvicorn src.api.main:app --reload
```

## Environment Variables

### LLM Providers (at least one required)

```bash
# Option 1: Groq (FREE)
GROQ_API_KEY=gsk_...

# Option 2: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Option 3: OpenAI
OPENAI_API_KEY=sk-...
```

### Embeddings (required for RAG)

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Infrastructure

```bash
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

### Monitoring (optional)

```bash
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_TRACING_V2=true
```

## Code Standards

- **Typing**: Full type hints with mypy strict mode
- **Formatting**: Ruff (line length 100)
- **Testing**: pytest with 98% coverage
- **Commits**: Conventional commits (feat/fix/docs/test/chore)

## API Endpoints

| Endpoint | Method | Rate Limit | Description |
|----------|--------|------------|-------------|
| `/health` | GET | - | Health check |
| `/analyze` | POST | 10/min | Run research analysis |
| `/quote/{ticker}` | GET | 30/min | Real-time stock quote |
| `/compare/{tickers}` | GET | 20/min | Compare P/E ratios (max 5) |

## Testing

Current status: **187 tests passing, 98% coverage**

```bash
# Quick test
pytest -q

# With coverage report
pytest --cov=src --cov-report=term-missing

# Single file
pytest tests/test_tools.py -v
```

## Deployment

### Azure Container Apps (Production)

Deployed via Terraform + GitHub Actions CI/CD:

```
API: https://equity-research-agent.thankfulhill-01e4fbbb.swedencentral.azurecontainerapps.io
Bot: equity-research-telegram-bot (internal)
```

**Infrastructure:**
- Azure Container Apps (serverless)
- Azure Container Registry (ACR)
- Azure OpenAI (embeddings + LLM)
- Qdrant (Azure Container Instance)
- Key Vault (secrets)

### CI/CD

GitHub Actions workflow (`.github/workflows/deploy.yml`):
1. Build Docker images
2. Push to ACR
3. Deploy to Container Apps

Triggered on push to `main`.

### Environment Variables (Azure)

Set via Terraform in `terraform/container_apps.tf`:
- `APP_ENV=production`
- `AZURE_OPENAI_*` (from Key Vault)
- `QDRANT_URL` (internal)
- `TELEGRAM_BOT_TOKEN` (for bot)

## Notes

- SEC EDGAR requires valid User-Agent with contact email
- yfinance has rate limits (~2000 req/hour)
- Qdrant runs on port 6333 (REST)
- Azure OpenAI embeddings: 1536 dimensions (ada-002)
- Groq model: llama-3.3-70b-versatile (free tier)

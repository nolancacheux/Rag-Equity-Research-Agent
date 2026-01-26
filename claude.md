# claude.md - Agent Instructions

## Project Overview

**Equity Research Agent** - AI-powered financial analysis using LangGraph, RAG, and real-time market data.

- **Production URL**: Configured via `API_BASE_URL` env var
- **Auth**: API key required for protected endpoints (`X-API-Key` header)
- **LLM Providers**: Groq (free), Azure OpenAI, OpenAI

## Architecture

```
src/
├── agents/           # LangGraph agents
│   ├── graph.py          # Main orchestration graph
│   ├── market_data.py    # yfinance integration
│   ├── document_reader.py # SEC filing RAG
│   ├── news_sentiment.py  # News analysis
│   └── synthesizer.py     # Report generation
├── api/              # FastAPI endpoints
│   ├── main.py           # REST API
│   ├── metrics.py        # Prometheus metrics
│   └── middleware/
│       └── auth.py       # API key authentication
├── config/           # Pydantic settings
│   └── settings.py       # Environment config
├── rag/              # RAG pipeline
│   ├── embeddings.py     # Azure OpenAI embeddings
│   ├── chunking.py       # Document chunking
│   └── vector_store.py   # Qdrant integration
├── telegram/         # Telegram bot
│   ├── bot.py            # Bot setup
│   ├── handlers.py       # Command handlers
│   ├── client.py         # API client
│   ├── formatters.py     # Message formatting
│   ├── keyboards.py      # Inline keyboards
│   └── i18n.py           # Translations (EN/FR)
├── tools/            # Data sources
│   ├── yfinance_tool.py  # Market data
│   ├── sec_edgar_tool.py # SEC filings
│   └── search_tool.py    # DuckDuckGo
└── utils/            # Utilities
    ├── cache.py          # Redis caching
    └── rate_limiter.py   # Rate limiting

terraform/            # Infrastructure as Code (Azure)
tests/                # Unit tests
docs/                 # Technical documentation
```

## Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | LangGraph | Agent workflow |
| LLM | Groq / Azure OpenAI / OpenAI | Analysis and synthesis |
| Embeddings | Azure OpenAI (ada-002) | 1536-dim vectors |
| Vector DB | Qdrant | Semantic search |
| API | FastAPI | REST endpoints |
| Bot | python-telegram-bot | Telegram interface |
| Data | yfinance, SEC EDGAR | Financial data |
| Cache | Redis | Response caching |
| Monitoring | Prometheus | Metrics |
| Infra | Terraform, Azure Container Apps | Deployment |

## API Endpoints

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/health` | GET | No | - | Health check |
| `/metrics` | GET | No | - | Prometheus metrics |
| `/analyze` | POST | **Yes** | 10/min | Run research analysis |
| `/quote/{ticker}` | GET | **Yes** | 30/min | Real-time stock quote |
| `/compare/{tickers}` | GET | **Yes** | 20/min | Compare P/E ratios |

### Authentication

Protected endpoints require `X-API-Key` header:
```bash
curl -H "X-API-Key: your-secret-key" https://your-api/quote/NVDA
```

Set via `API_SECRET_KEY` env var. If not set, auth is disabled (dev mode).

## Environment Variables

### Required (at least one LLM)

```bash
# Option 1: Groq (FREE - recommended)
GROQ_API_KEY=gsk_...

# Option 2: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Option 3: OpenAI
OPENAI_API_KEY=sk-...
```

### Infrastructure

```bash
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
SEC_USER_AGENT=YourApp your-email@example.com
```

### API Security (Production)

```bash
# Generate with: openssl rand -hex 32
API_SECRET_KEY=your-secret-key-here
```

### Telegram Bot

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
API_BASE_URL=https://your-api.azurecontainerapps.io
```

### Monitoring (optional)

```bash
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_TRACING_V2=true
```

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Lint & format
ruff check src/ --fix
ruff format src/

# Type check
mypy src/

# Run API locally
uvicorn src.api.main:app --reload

# Run Telegram bot
python run_telegram_bot.py

# Start all services (Docker)
docker compose up -d
```

## Code Standards

- **Typing**: Full type hints with mypy strict mode
- **Formatting**: Ruff (line length 100)
- **Testing**: pytest with 98% coverage minimum
- **Commits**: Conventional commits (feat/fix/docs/test/chore)
- **Security**: No hardcoded secrets, all via env vars

## Deployment

### Azure Container Apps (Production)

Deployed via Terraform + GitHub Actions CI/CD.

**Infrastructure:**
- Azure Container Apps (serverless, auto-scale)
- Azure Container Registry (ACR)
- Azure OpenAI (embeddings + LLM)
- Qdrant (managed)
- Key Vault (secrets)

### CI/CD Pipeline

GitHub Actions (`.github/workflows/`):
1. **ci.yml**: Lint, test, security scan
2. **deploy.yml**: Build → Push to ACR → Deploy to Container Apps

Triggered on push to `main`.

### Terraform

```bash
cd terraform
terraform init
terraform plan -var="telegram_bot_token=XXX" -var="sec_user_agent=XXX"
terraform apply
```

## Monitoring

### Prometheus Metrics (`/metrics`)

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Requests by method/endpoint/status |
| `http_request_duration_seconds` | Histogram | Request latency |
| `analysis_requests_total` | Counter | Analysis success/error |
| `analysis_duration_seconds` | Histogram | Analysis duration |
| `quote_requests_total` | Counter | Quotes by ticker |
| `errors_total` | Counter | Errors by type |

### LangSmith Tracing

Enable with `LANGCHAIN_TRACING_V2=true` to trace all LLM calls.

## Notes

- SEC EDGAR requires valid User-Agent with contact email
- yfinance has rate limits (~2000 req/hour)
- Groq free tier: llama-3.3-70b-versatile
- Azure OpenAI embeddings: 1536 dimensions (ada-002)
- Telegram bot supports EN/FR languages

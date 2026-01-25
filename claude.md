# claude.md - Agent Instructions

## Project Overview

**Equity Research Agent** - AI-powered financial analysis using LangGraph, RAG, and real-time market data.

**Deployed on Azure Container Apps** with Azure OpenAI for LLM and embeddings.

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
```

## Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | LangGraph | Agent workflow |
| LLM | Azure OpenAI (gpt-4o-mini) | Analysis & synthesis |
| Embeddings | Azure OpenAI (ada-002) | 1536-dim vectors |
| Vector DB | Qdrant | Semantic search |
| API | FastAPI | REST endpoints |
| Data | yfinance, SEC EDGAR | Financial data |
| Hosting | Azure Container Apps | Serverless containers |

## Azure Resources

| Resource | Name | Region |
|----------|------|--------|
| Resource Group | equity-research-rg | - |
| Container Apps | equity-research-agent | Sweden Central |
| Container Registry | cae661ada46dacr | Sweden Central |
| Azure OpenAI | equity-research-openai-se | Sweden Central |
| Qdrant | qdrant-vector-db | Sweden Central |

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

# Build & deploy to Azure
az acr build --registry cae661ada46dacr --image equity-research-agent:v6 .
az containerapp update --name equity-research-agent --resource-group equity-research-rg --image cae661ada46dacr.azurecr.io/equity-research-agent:v6
```

## Environment Variables

### Azure OpenAI (required)
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - API key
- `AZURE_OPENAI_DEPLOYMENT` - LLM deployment (gpt-4o-mini)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - Embeddings (text-embedding-ada-002)
- `AZURE_OPENAI_API_VERSION` - API version (2024-02-01)

### Qdrant
- `QDRANT_URL` - Qdrant endpoint

### Optional
- `LANGCHAIN_API_KEY` - LangSmith tracing
- `GROQ_API_KEY` - Alternative LLM (free tier)

## Code Standards

- **Typing**: Full type hints with mypy strict mode
- **Formatting**: Ruff (line length 100)
- **Testing**: pytest with 80%+ coverage target
- **Commits**: Conventional commits (feat/fix/docs/test/chore)

## API Endpoints

| Endpoint | Method | Rate Limit | Description |
|----------|--------|------------|-------------|
| `/health` | GET | - | Health check |
| `/analyze` | POST | 10/min | Run research analysis |
| `/quote/{ticker}` | GET | 30/min | Real-time stock quote |
| `/compare/{tickers}` | GET | 20/min | Compare P/E ratios (max 5)

## Live URLs

- **API**: https://equity-research-agent.wonderfulstone-1de7f015.swedencentral.azurecontainerapps.io
- **Health**: /health
- **Docs**: /docs

## Notes

- SEC EDGAR requires valid User-Agent with contact email
- yfinance has rate limits (~2000 req/hour)
- Qdrant runs on port 6333 (REST)
- Azure OpenAI embeddings: 1536 dimensions (ada-002)
- Cold start: ~10-30s when scaled to zero

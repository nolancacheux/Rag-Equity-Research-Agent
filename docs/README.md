# Documentation

Technical documentation for the Equity Research Agent project.

## Index

| Document | Description |
|----------|-------------|
| [azure-deployment.md](./azure-deployment.md) | Azure Deployment (Container Apps, OpenAI) |
| [terraform/](../terraform/README.md) | Infrastructure as Code (recommended) |
| [qdrant-vector-database.md](./qdrant-vector-database.md) | Vector database for RAG |
| [langgraph-orchestration.md](./langgraph-orchestration.md) | Agent orchestration with LangGraph |
| [redis-caching.md](./redis-caching.md) | Redis caching for API calls |
| [embeddings-rag.md](./embeddings-rag.md) | RAG pipeline and embedding model |
| [fastapi-backend.md](./fastapi-backend.md) | FastAPI REST API |
| [docker-setup.md](./docker-setup.md) | Docker Compose configuration |
| [financial-data-tools.md](./financial-data-tools.md) | Data sources (yfinance, SEC, DuckDuckGo) |
| [telegram-bot.md](./telegram-bot.md) | Telegram bot interface |
| [ci-cd-setup.md](./ci-cd-setup.md) | CI/CD with GitHub Actions |

## Project Structure

```
equity-research-agent/
├── src/
│   ├── agents/          # LangGraph agents
│   ├── api/             # FastAPI endpoints
│   ├── config/          # Pydantic configuration
│   ├── rag/             # RAG pipeline (embeddings, chunking, vector store)
│   ├── telegram/        # Telegram bot
│   ├── tools/           # Data fetching tools
│   └── utils/           # Utilities (cache, rate limiter)
├── terraform/           # Infrastructure as Code (Azure)
├── tests/               # Unit tests
├── docs/                # This documentation
├── docker-compose.yml   # Services orchestration
├── Dockerfile.api       # API image
├── Dockerfile.bot       # Telegram bot image
└── pyproject.toml       # Dependencies & config
```

## Quick Start

```bash
# 1. Configure environment variables
cp .env.example .env
# Edit .env with your API keys (at minimum: GROQ_API_KEY or OPENAI_API_KEY)

# 2. Start services
docker-compose up -d

# 3. Test the API
curl http://localhost:8000/health
```

## Contributing

When adding a new component:
1. Create documentation in `docs/`
2. Update this index
3. Document the "why" (technical choices) as much as the "how"

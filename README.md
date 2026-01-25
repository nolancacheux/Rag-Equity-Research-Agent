# 📊 Real-Time Equity Research Agent

> AI-powered financial analysis agent that acts as an autonomous Quantitative Analyst, scanning real market data, SEC filings, and news to generate professional equity research reports.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/nolancacheux/equity-research-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/nolancacheux/equity-research-agent/actions/workflows/ci.yml)

## 🎯 What It Does

Ask a question like:

> "Analyze NVIDIA's current situation. Compare their P/E Ratio with AMD, and check their latest 10-K report for China-related risks."

The agent will:
1. **Fetch real-time market data** via Yahoo Finance (prices, P/E ratios, financials)
2. **Download & analyze SEC 10-K reports** using RAG (finds the exact paragraph about China risks)
3. **Search recent news** for market sentiment
4. **Synthesize everything** into a professional research report with citations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph Orchestrator                  │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│  Market     │  Document   │    News     │   Synthesizer    │
│  Data Agent │  Reader     │  Sentiment  │   Agent          │
├─────────────┼─────────────┼─────────────┼──────────────────┤
│  yfinance   │  SEC EDGAR  │  DuckDuckGo │   Azure OpenAI   │
│  (+ Cache)  │  + RAG      │  Search     │   (GPT-4o)       │
└─────────────┴─────────────┴─────────────┴──────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         Qdrant          Redis          LangSmith
       (Vector DB)      (Cache)       (Monitoring)
```

## ⚡ Features

| Feature | Description |
|---------|-------------|
| **Real Market Data** | Live prices, financials, ratios via yfinance |
| **SEC 10-K Analysis** | Automatic download & RAG search on annual reports |
| **News Sentiment** | Real-time news search with DuckDuckGo |
| **Production-Ready** | Caching, rate limiting, security hardening |
| **Observable** | Full tracing with LangSmith |
| **Cloud-Native** | Azure Container Apps deployment ready |

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| **LLM** | Azure OpenAI (GPT-4o-mini) |
| **Orchestration** | LangGraph, LangChain |
| **Data Sources** | yfinance, SEC EDGAR, DuckDuckGo |
| **RAG** | Qdrant, Sentence Transformers |
| **API** | FastAPI, Pydantic |
| **Cache** | Redis |
| **Infrastructure** | Azure Container Apps, Docker |
| **CI/CD** | GitHub Actions |
| **Monitoring** | LangSmith, structlog |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Azure OpenAI resource (or OpenAI API key for dev)

### Local Development

```bash
# Clone
git clone https://github.com/nolancacheux/equity-research-agent.git
cd equity-research-agent

# Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Start services
docker compose up -d

# Check health
curl http://localhost:8000/health
```

### Configuration

Edit `.env` with your credentials:

```bash
# Azure OpenAI (Recommended for production)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# OR OpenAI Direct (Development only)
OPENAI_API_KEY=sk-...
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/analyze` | POST | Run full research analysis |
| `/quote/{ticker}` | GET | Get real-time stock quote |
| `/compare/{tickers}` | GET | Compare P/E ratios (comma-separated) |

### Example: Full Analysis

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze NVDA vs AMD. Check NVIDIA 10-K for China supply chain risks.",
    "tickers": ["NVDA", "AMD"]
  }'
```

### Example: Quick Quote

```bash
curl http://localhost:8000/quote/NVDA
```

### Example: Compare Stocks

```bash
curl http://localhost:8000/compare/NVDA,AMD,INTC
```

## 📁 Project Structure

```
equity-research-agent/
├── src/
│   ├── agents/          # LangGraph agents
│   │   ├── graph.py     # Orchestration
│   │   ├── market_data.py
│   │   ├── document_reader.py
│   │   ├── news_sentiment.py
│   │   └── synthesizer.py
│   ├── api/             # FastAPI
│   ├── config/          # Pydantic settings
│   ├── rag/             # Vector store & embeddings
│   ├── tools/           # Data integrations
│   └── utils/           # Cache, rate limiting
├── tests/               # Unit tests
├── docs/                # Technical documentation
├── infra/               # Azure Bicep templates
├── docker-compose.yml   # Local development
├── Dockerfile           # Production image
└── pyproject.toml
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=src

# Lint
ruff check src/

# Type check
mypy src/
```

## ☁️ Azure Deployment

### One-Command Deploy

```bash
# Set credentials
export AZURE_OPENAI_API_KEY=your-key

# Deploy to Azure Container Apps
./infra/deploy.sh
```

### Manual Deploy

See [docs/azure-deployment.md](docs/azure-deployment.md) for detailed instructions.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [claude.md](claude.md) | Agent instructions |
| [docs/azure-deployment.md](docs/azure-deployment.md) | Azure setup guide |
| [docs/langgraph-orchestration.md](docs/langgraph-orchestration.md) | Agent workflow |
| [docs/qdrant-vector-database.md](docs/qdrant-vector-database.md) | RAG setup |
| [docs/embeddings-rag.md](docs/embeddings-rag.md) | Embeddings pipeline |

## 🔒 Security

- Rate limiting (10 req/min for analysis, 30/min for quotes)
- Input validation with Pydantic
- No credentials in code (env-based config)
- Error masking in production
- CORS restricted in production

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

Built with AI & ML engineering best practices.

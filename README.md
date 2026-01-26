# Equity Research Agent

[![CI](https://github.com/nolancacheux/equity-research-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/nolancacheux/equity-research-agent/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered autonomous quantitative analyst. Fetches real-time market data, SEC filings, earnings calls, and social sentiment to generate professional equity research reports.

**Author:** [Nolan Cacheux](https://github.com/nolancacheux) · [LinkedIn](https://www.linkedin.com/in/nolancacheux/)

---

## Features

| Category | Capabilities |
|----------|-------------|
| **Market Data** | Real-time quotes, financials, peer comparison via Yahoo Finance |
| **SEC Analysis** | 10-K/10-Q filing search with hybrid RAG (BM25 + dense embeddings) |
| **Sentiment** | Reddit (WSB, r/stocks), news aggregation, earnings call transcripts |
| **Valuation** | DCF model, risk scoring (1-10), historical analysis |
| **Alerts** | Watchlist, price alerts, P/E threshold notifications |

## Architecture

```
┌──────────────────────────────────────────────────────┐
│               LangGraph Orchestrator                  │
├──────────────────────────────────────────────────────┤
│  Market Data ─┬─ SEC RAG ─┬─ Sentiment ─┬─ Earnings  │
│      Agent    │   Agent   │    Agent    │   Agent    │
└───────────────┴───────────┴─────────────┴────────────┘
                            │
                    ┌───────▼───────┐
                    │  Synthesizer  │
                    │    Agent      │
                    └───────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- Docker (for Qdrant/Redis)

### Installation

```bash
git clone https://github.com/nolancacheux/equity-research-agent.git
cd equity-research-agent

# Install dependencies
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Add GROQ_API_KEY (free at console.groq.com)
```

### Run

```bash
# Start vector DB + cache
docker-compose up -d qdrant redis

# API
uvicorn src.api.main:app --reload

# Telegram bot (separate terminal)
python -m src.telegram.bot
```

### Development

```bash
uv run pytest                    # Tests
uv run ruff check --fix src/     # Lint
uv run ruff format src/          # Format
```

---

## API

| Endpoint | Description |
|----------|-------------|
| `GET /quote/{ticker}` | Real-time stock quote |
| `GET /compare/{tickers}` | Side-by-side comparison |
| `POST /analyze` | Full research analysis |
| `GET /dcf/{ticker}` | DCF fair value |
| `GET /risk/{ticker}` | 10-K risk score |
| `GET /reddit/{ticker}` | Reddit sentiment |
| `GET /peers/{ticker}` | Peer comparison |

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/q NVDA` | Quick quote |
| `/analyze <query>` | Deep analysis |
| `/dcf NVDA` | DCF valuation |
| `/risk NVDA` | Risk score |
| `/watchlist` | Manage watchlist |
| `/alert NVDA above 150` | Price alert |

---

## Azure Deployment

Deploys to **Azure Container Apps** via GitHub Actions.

### Resources

| Resource | Purpose |
|----------|---------|
| Container Registry | Docker images |
| Container Apps | API + Bot hosting |
| Qdrant + Redis | Vector DB + Cache |

### Setup

1. **Terraform init:**
```bash
cd terraform && terraform init
terraform apply
```

2. **GitHub Secrets:**
```
AZURE_CREDENTIALS, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID
ACR_LOGIN_SERVER, ACR_USERNAME, ACR_PASSWORD
TELEGRAM_BOT_TOKEN, GROQ_API_KEY
```

3. **Push to `main`** → Auto-deploy

### Manual Deploy

```bash
az acr login --name equityresearchacr
docker build -t equityresearchacr.azurecr.io/equity-research-api:latest -f Dockerfile.api .
docker push equityresearchacr.azurecr.io/equity-research-api:latest
az containerapp update --name equity-research-api --resource-group equity-research-rg \
  --image equityresearchacr.azurecr.io/equity-research-api:latest
```

**Estimated cost:** ~$5-15/month (consumption plan, scales to zero)

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **LLM** | Groq (Llama 3.3 70B), Azure OpenAI, OpenAI |
| **Orchestration** | LangGraph, LangChain |
| **RAG** | Qdrant, Hybrid Search (BM25 + dense), Reranking |
| **Data** | yfinance, SEC EDGAR, Reddit API, DuckDuckGo |
| **Backend** | FastAPI, Pydantic, Redis |
| **Bot** | python-telegram-bot |
| **Infra** | Docker, Azure Container Apps, Terraform, GitHub Actions |
| **Tooling** | uv, Ruff, pytest |

## Project Structure

```
src/
├── agents/       # LangGraph agents (market, SEC, sentiment, synthesizer)
├── services/     # Business logic (DCF, risk scoring, watchlist)
├── tools/        # Data fetchers (yfinance, SEC, Reddit)
├── rag/          # Hybrid search, chunking, reranking
├── api/          # FastAPI endpoints
└── telegram/     # Bot handlers
terraform/        # Azure IaC
tests/            # pytest suite
```

## License

MIT

# Real-Time Equity Research Agent

AI-powered financial analysis agent that acts as an autonomous Quantitative Analyst, scanning real market data, SEC filings, earnings calls, and social sentiment to generate professional equity research reports.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

---

**Author:** [Nolan Cacheux](https://github.com/nolancacheux)  
**GitHub:** [github.com/nolancacheux](https://github.com/nolancacheux)  
**LinkedIn:** [linkedin.com/in/nolancacheux](https://www.linkedin.com/in/nolancacheux/)

---

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
| **Deep Analysis** | Multi-source research with SEC filings, news, earnings calls |
| **Real-time Quotes** | Live prices, P/E, market cap, volume |
| **Stock Comparison** | Side-by-side metrics comparison |

### Advanced Tools
| Tool | Command | Description |
|------|---------|-------------|
| **DCF Valuation** | `/dcf NVDA` | Calculate fair value using discounted cash flow |
| **Risk Score** | `/risk NVDA` | 10-K risk analysis with score 1-10 |
| **Peer Comparison** | `/peers NVDA` | Compare vs industry competitors |
| **Reddit Sentiment** | `/reddit NVDA` | WSB/stocks/investing sentiment |
| **Earnings Calendar** | `/calendar` | Upcoming earnings dates |
| **Historical Analysis** | `/history NVDA` | Price history & earnings reactions |

### Watchlist & Alerts
| Feature | Command | Description |
|---------|---------|-------------|
| **Watchlist** | `/watchlist` | Track your favorite stocks |
| **Add Stock** | `/watchlist add NVDA` | Add to watchlist |
| **Price Alert** | `/alert NVDA above 150` | Get notified when price crosses threshold |
| **P/E Alert** | `/alert AAPL pe_above 30` | Alert on valuation metrics |

### Data Sources (All Free)
| Source | Description |
|--------|-------------|
| **Yahoo Finance** | Real-time prices, financials, ratios, history |
| **SEC EDGAR** | 10-K annual reports with RAG search |
| **Earnings Calls** | Transcripts from aggregators |
| **Reddit** | r/wallstreetbets, r/stocks, r/investing |
| **DuckDuckGo** | Real-time financial news |

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

---

## Local Development

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker & Docker Compose (for dependencies)

### 1. Clone and Setup

```bash
git clone https://github.com/nolancacheux/equity-research-agent.git
cd equity-research-agent
```

### 2. Install with uv (Recommended)

```bash
# Install uv if not installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

uv pip install -e ".[dev]"
```

### Alternative: Install with pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required:**
- `GROQ_API_KEY` - Free at [console.groq.com](https://console.groq.com)

**Optional:**
- `AZURE_OPENAI_*` - Azure OpenAI credentials
- `OPENAI_API_KEY` - OpenAI API key
- `LANGCHAIN_API_KEY` - LangSmith monitoring

### 4. Start Dependencies

```bash
docker-compose up -d qdrant redis
```

### 5. Run the Application

```bash
# API Server
uvicorn src.api.main:app --reload --port 8000

# Telegram Bot (separate terminal)
python -m src.telegram.bot
```

### 6. Run Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html
```

### 7. Lint & Format

```bash
# Check
uv run ruff check .
uv run ruff format --check .

# Fix
uv run ruff check --fix .
uv run ruff format .
```

---

## Azure Deployment

This project is configured for deployment on **Azure Container Apps** with full CI/CD via GitHub Actions.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Cloud                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  Container App  │    │  Container App  │                     │
│  │     (API)       │    │     (Bot)       │                     │
│  │   Port 8000     │    │   Telegram      │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           └──────────┬───────────┘                               │
│                      │                                           │
│  ┌───────────────────▼───────────────────┐                      │
│  │       Container Apps Environment       │                      │
│  │         (equity-research-env)          │                      │
│  └───────────────────┬───────────────────┘                      │
│                      │                                           │
│  ┌───────────────────▼───────────────────┐                      │
│  │      Azure Container Registry          │                      │
│  │        (equityresearchacr)             │                      │
│  └───────────────────────────────────────┘                      │
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │     Qdrant      │    │     Redis       │                     │
│  │  (Vector DB)    │    │    (Cache)      │                     │
│  │  Container App  │    │  Container App  │                     │
│  └─────────────────┘    └─────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Azure Resources

| Resource | Type | Purpose |
|----------|------|---------|
| `equity-research-rg` | Resource Group | All resources |
| `equityresearchacr` | Container Registry | Docker images |
| `equity-research-env` | Container Apps Environment | Hosting |
| `equity-research-api` | Container App | FastAPI backend |
| `equity-research-bot` | Container App | Telegram bot |
| `equity-research-qdrant` | Container App | Vector database |
| `equity-research-redis` | Container App | Cache |

### Prerequisites

1. **Azure Account** with active subscription
2. **Azure CLI** installed and logged in
3. **GitHub repository** with Actions enabled

### Initial Setup

#### 1. Create Azure Resources (Terraform)

```bash
cd terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
resource_group_name = "equity-research-rg"
location            = "swedencentral"
acr_name            = "equityresearchacr"
environment_name    = "equity-research-env"
telegram_bot_token  = "your-telegram-bot-token"
groq_api_key        = "your-groq-api-key"
EOF

# Plan and apply
terraform plan
terraform apply
```

#### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository (`Settings > Secrets > Actions`):

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON |
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `ACR_LOGIN_SERVER` | `equityresearchacr.azurecr.io` |
| `ACR_USERNAME` | ACR admin username |
| `ACR_PASSWORD` | ACR admin password |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `GROQ_API_KEY` | Groq API key |

#### 3. Create Service Principal

```bash
# Create service principal with Contributor role
az ad sp create-for-rbac \
  --name "equity-research-github" \
  --role Contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/equity-research-rg \
  --json-auth

# Output goes into AZURE_CREDENTIALS secret
```

### CI/CD Pipeline

The project uses two GitHub Actions workflows:

#### CI Workflow (`.github/workflows/ci.yml`)
- Runs on every push and PR
- Linting with Ruff
- Security scan with Bandit
- Unit tests with pytest
- Coverage reporting

#### Build & Deploy (`.github/workflows/deploy.yml`)
- Runs on push to `main`
- Builds Docker images
- Pushes to Azure Container Registry
- Deploys to Azure Container Apps

### Manual Deployment

```bash
# Login to Azure
az login

# Login to ACR
az acr login --name equityresearchacr

# Build and push images
docker build -t equityresearchacr.azurecr.io/equity-research-api:latest -f Dockerfile.api .
docker build -t equityresearchacr.azurecr.io/equity-research-bot:latest -f Dockerfile.bot .
docker push equityresearchacr.azurecr.io/equity-research-api:latest
docker push equityresearchacr.azurecr.io/equity-research-bot:latest

# Deploy API
az containerapp update \
  --name equity-research-api \
  --resource-group equity-research-rg \
  --image equityresearchacr.azurecr.io/equity-research-api:latest

# Deploy Bot
az containerapp update \
  --name equity-research-bot \
  --resource-group equity-research-rg \
  --image equityresearchacr.azurecr.io/equity-research-bot:latest
```

### Environment Variables (Azure)

Set these in Azure Container Apps configuration:

```bash
# API Container
GROQ_API_KEY=<from-secret>
QDRANT_URL=http://equity-research-qdrant
REDIS_URL=redis://equity-research-redis:6379
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<optional>

# Bot Container
TELEGRAM_BOT_TOKEN=<from-secret>
API_URL=http://equity-research-api:8000
```

### Monitoring

```bash
# View logs
az containerapp logs show \
  --name equity-research-api \
  --resource-group equity-research-rg \
  --follow

# Check status
az containerapp show \
  --name equity-research-api \
  --resource-group equity-research-rg \
  --query "properties.runningStatus"
```

### Costs

Estimated monthly cost with minimal usage:
- Container Apps: ~$0-10 (consumption plan, scales to zero)
- Container Registry: ~$5 (Basic tier)
- **Total: ~$5-15/month**

---

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
- `/reddit <ticker>` - Reddit sentiment
- `/calendar` - Earnings calendar
- `/history <ticker>` - Price history

### Watchlist Commands
- `/watchlist` or `/wl` - View watchlist
- `/watchlist add <ticker>` - Add stock
- `/alert <ticker> above <price>` - Price alert

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
| **Infra** | Docker, Azure Container Apps, Terraform |
| **CI/CD** | GitHub Actions |
| **Package Manager** | uv |

## Project Structure

```
equity-research-agent/
├── src/
│   ├── agents/              # LangGraph agents
│   │   ├── graph.py         # Main orchestration
│   │   ├── market_data.py   # Yahoo Finance
│   │   ├── document_reader.py # SEC RAG
│   │   └── synthesizer.py   # Report generation
│   ├── services/            # Business logic
│   │   ├── watchlist.py     # Watchlist & alerts
│   │   ├── dcf_valuation.py # DCF calculator
│   │   └── risk_scoring.py  # Risk scoring
│   ├── tools/               # Data fetchers
│   │   ├── yfinance_tool.py
│   │   └── sec_edgar_tool.py
│   ├── rag/                 # RAG components
│   │   ├── hybrid_search.py
│   │   └── vector_store.py
│   ├── api/                 # FastAPI backend
│   │   └── main.py
│   └── telegram/            # Telegram bot
│       ├── bot.py
│       └── handlers.py
├── terraform/               # Infrastructure as Code
├── tests/                   # Test suite
├── pyproject.toml           # Project config (uv/pip)
├── Dockerfile.api           # API container
├── Dockerfile.bot           # Bot container
└── docker-compose.yml       # Local development
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

PRs welcome! Please:
1. Follow existing code style (ruff)
2. Add tests for new features
3. Update documentation

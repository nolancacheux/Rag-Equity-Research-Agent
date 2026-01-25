# Real-Time Equity Research Agent

AI-powered financial analysis agent that acts as an autonomous Quantitative Analyst, scanning real market data, SEC filings, and news to generate professional equity research reports.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/nolancacheux/equity-research-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/nolancacheux/equity-research-agent/actions/workflows/ci.yml)
[![Deploy](https://github.com/nolancacheux/equity-research-agent/actions/workflows/deploy.yml/badge.svg)](https://github.com/nolancacheux/equity-research-agent/actions/workflows/deploy.yml)

## Live Demo

**API:** https://<your-app>.azurecontainerapps.io

```bash
# Health check
curl https://<your-app>.azurecontainerapps.io/health

# Get NVIDIA quote
curl https://<your-app>.azurecontainerapps.io/quote/NVDA
```

## What It Does

Ask a question like:

> "Analyze NVIDIA's current situation. Compare their P/E Ratio with AMD, and check their latest 10-K report for China-related risks."

The agent will:
1. **Fetch real-time market data** via Yahoo Finance (prices, P/E ratios, financials)
2. **Download and analyze SEC 10-K reports** using RAG (finds the exact paragraph about China risks)
3. **Search recent news** for market sentiment
4. **Synthesize everything** into a professional research report with citations

## Architecture

```
+-------------------------------------------------------------+
|                      LangGraph Orchestrator                  |
+-------------+-------------+-------------+-------------------+
|  Market     |  Document   |    News     |   Synthesizer     |
|  Data Agent |  Reader     |  Sentiment  |   Agent           |
+-------------+-------------+-------------+-------------------+
|  yfinance   |  SEC EDGAR  |  DuckDuckGo |   Groq / OpenAI   |
|  (+ Cache)  |  + RAG      |  Search     |   (LLM)           |
+-------------+-------------+-------------+-------------------+
                              |
              +---------------+---------------+
              |               |               |
         Qdrant          Redis          LangSmith
       (Vector DB)      (Cache)       (Monitoring)
```

## Features

| Feature | Description |
|---------|-------------|
| **Real Market Data** | Live prices, financials, ratios via yfinance |
| **SEC 10-K Analysis** | Automatic download and RAG search on annual reports |
| **News Sentiment** | Real-time news search with DuckDuckGo |
| **Zero-Cost LLM Option** | Groq free tier supported (Llama 3.3 70B) |
| **Production-Ready** | Caching, rate limiting, security hardening |
| **Observable** | Full tracing with LangSmith |
| **Cloud-Native** | Docker and Azure Container Apps ready |

## Tech Stack

| Category | Technologies |
|----------|--------------|
| **LLM** | Groq (free), Azure OpenAI, OpenAI |
| **Orchestration** | LangGraph, LangChain |
| **Data Sources** | yfinance, SEC EDGAR, DuckDuckGo |
| **RAG** | Qdrant, Azure OpenAI Embeddings |
| **API** | FastAPI, Pydantic |
| **Cache** | Redis |
| **Infrastructure** | Docker, Azure Container Apps |
| **CI/CD** | GitHub Actions |
| **Monitoring** | LangSmith, structlog |

## Quick Start

### Option A: Local Development (Recommended to start)

**Prerequisites:** Python 3.11+, Docker, Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/nolancacheux/equity-research-agent.git
cd equity-research-agent

# 2. Configure environment
cp .env.example .env
# Edit .env - add at least one LLM provider:
#   GROQ_API_KEY=gsk_...        (FREE - recommended)
#   or OPENAI_API_KEY=sk-...    (paid)

# 3. Start all services (API + Qdrant + Redis)
docker compose up -d

# 4. Verify it works
curl http://localhost:8000/health
curl http://localhost:8000/quote/NVDA
```

**Add Telegram bot (optional):**
```bash
# Add to .env:
TELEGRAM_BOT_TOKEN=your_token_from_botfather

# Start the bot
python run_telegram_bot.py
```

### Option B: Deploy to Azure

**Prerequisites:** Azure CLI, Terraform 1.5+, Azure subscription

```bash
# 1. Login to Azure
az login

# 2. Create Terraform state backend (one-time)
az group create -n terraform-state-rg -l swedencentral
az storage account create -n tfstateequityresearch -g terraform-state-rg -l swedencentral --sku Standard_LRS
az storage container create -n tfstate --account-name tfstateequityresearch

# 3. Configure secrets
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your TELEGRAM_BOT_TOKEN

# 4. Deploy infrastructure + containers
./scripts/deploy.sh full

# Your API will be available at: https://<app-name>.azurecontainerapps.io
```

See [docs/ci-cd-setup.md](docs/ci-cd-setup.md) for CI/CD automation setup.

### Configuration

Edit `.env` with your credentials:

```bash
# LLM Provider (choose one)
GROQ_API_KEY=gsk_...                      # FREE tier - recommended for dev
OPENAI_API_KEY=sk-...                     # Paid
AZURE_OPENAI_ENDPOINT=https://...         # Enterprise

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=123456789:ABC...
```

## Telegram Bot

Interact with the agent directly from Telegram!

### Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Copy the bot token to your `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   API_BASE_URL=http://localhost:8000
   ```
3. Start the API (if not running):
   ```bash
   docker compose up -d
   ```
4. Run the bot:
   ```bash
   python run_telegram_bot.py
   ```

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/quote <TICKER>` | Get real-time stock quote | `/quote NVDA` |
| `/compare <T1,T2,...>` | Compare multiple stocks | `/compare NVDA,AMD,INTC` |
| `/analyze <query>` | Run full AI analysis | `/analyze Analyze NVIDIA vs AMD` |
| `/help` | Show available commands | `/help` |

Short aliases: `/q` (quote), `/c` (compare), `/a` (analyze)

## API Endpoints

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

## Project Structure

```
equity-research-agent/
├── src/
│   ├── agents/          # LangGraph agents
│   │   ├── graph.py     # Orchestration
│   │   ├── market_data.py
│   │   ├── document_reader.py
│   │   ├── news_sentiment.py
│   │   └── synthesizer.py
│   ├── api/             # FastAPI application
│   ├── config/          # Pydantic settings
│   ├── rag/             # Vector store and embeddings
│   ├── telegram/        # Telegram bot
│   │   ├── bot.py       # Entry point
│   │   ├── handlers.py  # Command handlers
│   │   ├── client.py    # API client
│   │   └── formatters.py
│   ├── tools/           # Data integrations
│   └── utils/           # Cache, rate limiting
├── tests/               # Unit tests (89% coverage)
├── docs/                # Technical documentation
├── terraform/           # Azure infrastructure as code
├── scripts/             # Deployment scripts
├── docker-compose.yml   # Local development (API + Bot)
├── Dockerfile.api       # API container
├── Dockerfile.bot       # Telegram bot container
└── pyproject.toml
```

## Testing

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

## Deployment

### Local Only
```bash
docker compose up -d          # Start everything
docker compose logs -f api    # View API logs
docker compose down           # Stop
```

### Azure (Manual)
```bash
./scripts/deploy.sh full      # One-command deploy
```

### CI/CD Pipeline

The GitHub Actions workflow runs automatically on push/PR:
- **Lint** → Ruff linter and formatter
- **Test** → Pytest with 89% coverage
- **Security** → Bandit security scan
- **Build** → Docker images (API + Bot)
- **Terraform** → Validate infrastructure code

Deployment to Azure is **manual** via `./scripts/deploy.sh`. See [docs/ci-cd-setup.md](docs/ci-cd-setup.md) to enable auto-deploy.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ci-cd-setup.md](docs/ci-cd-setup.md) | CI/CD pipeline with Terraform |
| [docs/telegram-bot.md](docs/telegram-bot.md) | Telegram bot setup & commands |
| [docs/azure-deployment.md](docs/azure-deployment.md) | Azure setup guide |
| [docs/langgraph-orchestration.md](docs/langgraph-orchestration.md) | Agent workflow |
| [docs/qdrant-vector-database.md](docs/qdrant-vector-database.md) | RAG setup |
| [docs/embeddings-rag.md](docs/embeddings-rag.md) | Embeddings pipeline |

## Security

- Rate limiting (10 req/min for analysis, 30/min for quotes)
- Input validation with Pydantic
- No credentials in code (env-based config)
- Error masking in production
- CORS restricted in production

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Nolan Cacheux** - AI/ML Engineer

- GitHub: [@nolancacheux](https://github.com/nolancacheux)
- LinkedIn: [nolancacheux](https://linkedin.com/in/nolancacheux)

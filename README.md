# 📊 Real-Time Equity Research Agent

> AI-powered financial analysis agent that acts as an autonomous Quantitative Analyst, scanning real market data, SEC filings, and news to generate professional equity research reports.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

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
│  yfinance   │  SEC EDGAR  │  DuckDuckGo │   LLM            │
│  (+ Cache)  │  + RAG      │  Search     │   Compilation    │
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
| **UK Companies** | Companies House API integration (bonus) |
| **Production-Ready** | Caching, rate limiting, error handling |
| **Observable** | Full tracing with LangSmith |

## 🛠️ Tech Stack

- **Agents**: Python, LangGraph, LangChain
- **Data**: yfinance, sec-edgar-downloader, Companies House API
- **RAG**: Qdrant, Unstructured.io, Sentence Transformers
- **API**: FastAPI, Uvicorn
- **Cache**: Redis
- **Infra**: Azure Container Apps, GitHub Actions
- **Monitoring**: LangSmith

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis (optional, for caching)
- OpenAI API key

### Installation

```bash
# Clone the repo
git clone https://github.com/nolancacheux/equity-research-agent.git
cd equity-research-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Run the API

```bash
uvicorn src.api.main:app --reload
```

### Example Query

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze NVDA vs AMD P/E ratios and check NVIDIA 10-K for China risks"}'
```

## 📁 Project Structure

```
equity-research-agent/
├── src/
│   ├── agents/          # LangGraph agent definitions
│   ├── tools/           # Data source integrations
│   ├── rag/             # Vector store & chunking
│   ├── api/             # FastAPI endpoints
│   ├── config/          # Settings & configuration
│   └── utils/           # Cache, rate limiting, helpers
├── tests/               # Unit & integration tests
├── .github/workflows/   # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 🧪 Testing

```bash
pytest --cov=src
```

## 📦 Deployment

```bash
# Build Docker image
docker build -t equity-research-agent .

# Deploy to Azure Container Apps
az containerapp up --name equity-research-agent --source .
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Nolan Cacheux**
- GitHub: [@nolancacheux](https://github.com/nolancacheux)
- LinkedIn: [nolancacheux](https://www.linkedin.com/in/nolancacheux/)

# FastAPI Backend

## Overview

FastAPI powers all REST endpoints for the Equity Research Agent, including core analysis, advanced tools, and watchlist management.

## Architecture

```
src/api/
├── main.py              # All API endpoints
├── metrics.py           # Prometheus metrics
└── middleware/
    └── auth.py          # API key authentication
```

## All Endpoints

### Core Endpoints

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/health` | GET | No | - | Health check |
| `/metrics` | GET | No | - | Prometheus metrics |
| `/analyze` | POST | Yes | 10/min | Full research analysis |
| `/quote/{ticker}` | GET | Yes | 30/min | Real-time stock quote |
| `/compare/{tickers}` | GET | Yes | 20/min | Compare stocks |

### Tool Endpoints

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/dcf/{ticker}` | GET | Yes | 10/min | DCF fair value |
| `/risk/{ticker}` | GET | Yes | 10/min | Risk score (1-10) |
| `/peers/{ticker}` | GET | Yes | 10/min | Peer comparison |
| `/reddit/{ticker}` | GET | Yes | 15/min | Reddit sentiment |
| `/earnings/{ticker}` | GET | Yes | 10/min | Earnings call analysis |
| `/calendar` | GET | Yes | 10/min | Earnings calendar |
| `/history/{ticker}` | GET | Yes | 20/min | Historical analysis |

### Watchlist Endpoints

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/watchlist/{user_id}` | GET | Yes | 30/min | Get user watchlist |
| `/watchlist/{user_id}/add` | POST | Yes | 30/min | Add to watchlist |
| `/watchlist/{user_id}/alert` | POST | Yes | 20/min | Create price alert |

## Authentication

Protected endpoints require `X-API-Key` header when `API_SECRET_KEY` env var is set.

```bash
# Request with auth
curl -H "X-API-Key: your-secret-key" https://your-api/quote/NVDA

# Generate a key
openssl rand -hex 32
```

If `API_SECRET_KEY` is not set, authentication is disabled (dev mode).

## Endpoint Details

### POST /analyze

Full research analysis with optional feature flags.

**Request:**
```json
{
  "query": "Analyze NVDA and check their 10-K for China risks",
  "tickers": ["NVDA"]
}
```

**Response:**
```json
{
  "success": true,
  "report": {
    "title": "Equity Research: NVDA",
    "full_report": "# Equity Research...",
    "executive_summary": "...",
    "data_sources": ["Yahoo Finance", "SEC EDGAR", "DuckDuckGo News"]
  },
  "market_data": {"NVDA": {...}},
  "errors": []
}
```

### GET /dcf/{ticker}

Calculate fair value using DCF model.

**Example:** `GET /dcf/NVDA`

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "NVDA",
    "current_price": 142.50,
    "fair_value": 165.20,
    "upside_percent": 15.9,
    "fcf_current": 29500000000,
    "growth_rate": 0.15,
    "discount_rate": 0.10,
    "summary": "## DCF Valuation: NVDA\n..."
  }
}
```

### GET /risk/{ticker}

Risk assessment from 10-K filing.

**Example:** `GET /risk/NVDA`

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "NVDA",
    "overall_score": 6,
    "risk_breakdown": {
      "market": 3,
      "operational": 4,
      "financial": 2
    },
    "top_risks": [
      {"category": "geopolitical", "description": "China export controls...", "score": 4}
    ],
    "summary": "## Risk Assessment: NVDA\n..."
  }
}
```

### GET /peers/{ticker}

Compare with industry peers.

**Example:** `GET /peers/NVDA`

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "NVDA",
    "sector": "Semiconductors",
    "industry": "Semiconductors",
    "peers": ["AMD", "INTC", "QCOM", "AVGO"],
    "metrics": {
      "PE Ratio": {"NVDA": 65.2, "AMD": 45.8, "INTC": 22.1},
      "Market Cap": {"NVDA": 3500000000000, "AMD": 280000000000}
    },
    "ranking": {"PE Ratio": 4, "Market Cap": 1},
    "strengths": ["Best Market Cap among peers"],
    "weaknesses": ["Lowest PE Ratio among peers"],
    "summary": "## Peer Comparison: NVDA\n..."
  }
}
```

### GET /reddit/{ticker}

Reddit sentiment analysis.

**Example:** `GET /reddit/NVDA`

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "NVDA",
    "sentiment_score": 0.35,
    "sentiment_label": "bullish",
    "total_mentions": 156,
    "bullish_ratio": 0.68,
    "trending_topics": ["AI", "earnings", "datacenter"],
    "top_discussions": [
      {"title": "NVDA earnings tomorrow!", "subreddit": "wallstreetbets", "sentiment": "bullish"}
    ],
    "summary": "## Reddit Sentiment: NVDA\n..."
  }
}
```

### GET /calendar

Earnings calendar.

**Example:** `GET /calendar?tickers=NVDA,AAPL`

**Response:**
```json
{
  "success": true,
  "data": {
    "this_week": [
      {"ticker": "NVDA", "date": "2026-01-28", "days": 2}
    ],
    "watchlist": [...],
    "major": [...],
    "summary": "## Earnings Calendar\n..."
  }
}
```

### GET /history/{ticker}

Historical analysis.

**Example:** `GET /history/NVDA?analysis=earnings`

**Response:**
```json
{
  "success": true,
  "type": "earnings_reactions",
  "data": {
    "ticker": "NVDA",
    "avg_move": 8.5,
    "beat_rate": 0.875,
    "reactions": [
      {"quarter": "Q3 2025", "change": 12.3},
      {"quarter": "Q2 2025", "change": -5.2}
    ],
    "summary": "## Earnings Reaction Pattern: NVDA\n..."
  }
}
```

### GET /watchlist/{user_id}

Get user's watchlist and alerts.

**Response:**
```json
{
  "success": true,
  "data": {
    "tickers": ["NVDA", "AAPL", "TSLA"],
    "items": [
      {"ticker": "NVDA", "added": "2026-01-25", "notes": "AI play"}
    ],
    "alerts": [
      {"id": "abc123", "ticker": "NVDA", "type": "price_above", "threshold": 150}
    ]
  }
}
```

### POST /watchlist/{user_id}/add

Add to watchlist.

**Example:** `POST /watchlist/123/add?ticker=NVDA&notes=AI%20play`

### POST /watchlist/{user_id}/alert

Create price alert.

**Example:** `POST /watchlist/123/alert?ticker=NVDA&alert_type=price_above&threshold=150`

**Alert types:** `price_above`, `price_below`, `pe_above`, `pe_below`

## Rate Limiting

Implemented with `slowapi`:

```python
@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze(request: Request, ...):
    ...
```

## Running

```bash
# Development
uvicorn src.api.main:app --reload

# Production
docker compose up -d
```

## API Docs

- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

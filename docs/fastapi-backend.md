# FastAPI Backend

## Why FastAPI?

FastAPI is the web framework for exposing the financial research API.

### Advantages

| Criteria | FastAPI | Flask | Django |
|----------|---------|-------|--------|
| **Performance** | Native async | Sync | Sync |
| **Typing** | Native Pydantic | Manual | Manual |
| **OpenAPI** | Auto-generated | Manual | DRF |
| **Validation** | Automatic | Manual | Serializers |

### Reasons for Choice

1. **Native async**: Perfect for I/O-bound operations (API calls, DB)
2. **Pydantic**: Automatic validation + serialization
3. **OpenAPI**: Auto-generated Swagger documentation
4. **Performance**: One of the fastest Python frameworks

## Architecture

```
src/api/
├── main.py              # API endpoints
├── metrics.py           # Prometheus metrics
└── middleware/
    └── auth.py          # API key authentication
```

## Endpoints

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/health` | GET | No | - | Health check |
| `/metrics` | GET | No | - | Prometheus metrics |
| `/analyze` | POST | **Yes** | 10/min | Run research analysis |
| `/quote/{ticker}` | GET | **Yes** | 30/min | Real-time stock quote |
| `/compare/{tickers}` | GET | **Yes** | 20/min | Compare P/E ratios |

## Authentication

Protected endpoints require `X-API-Key` header when `API_SECRET_KEY` env var is set.

```bash
# Request with auth
curl -H "X-API-Key: your-secret-key" https://your-api/quote/NVDA

# Generate a key
openssl rand -hex 32
```

### Implementation

```python
# src/api/middleware/auth.py
async def verify_api_key(request: Request) -> None:
    api_key = os.environ.get("API_SECRET_KEY")
    if not api_key:
        return  # Auth disabled in dev
    
    request_key = request.headers.get("X-API-Key")
    if request_key != api_key:
        raise HTTPException(401, "Invalid API key")
```

## Endpoint Details

### GET /health

Health check for monitoring (no auth required).

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production"
}
```

### GET /metrics

Prometheus metrics endpoint (no auth required).

**Response:** Prometheus text format
```
# HELP http_requests_total Total HTTP requests
http_requests_total{method="GET",endpoint="/health",status="200"} 5.0
# HELP analysis_duration_seconds Analysis duration
analysis_duration_seconds_sum 45.2
```

### POST /analyze

Run a financial research analysis.

**Request:**
```json
{
  "query": "Analyze NVDA and check their 10-K for China supply chain risks",
  "tickers": ["NVDA"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Research query (10-1000 chars) |
| `tickers` | string[] | Optional, max 5 (auto-detected if not provided) |

**Response:**
```json
{
  "success": true,
  "report": {
    "title": "...",
    "full_report": "...",
    "executive_summary": "..."
  },
  "market_data": {
    "NVDA": {...}
  },
  "errors": []
}
```

### GET /quote/{ticker}

Get real-time quote for a stock.

**Example:** `GET /quote/NVDA`

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "price": 875.50,
    "pe_ratio": 65.2,
    "market_cap": 2150000000000,
    "volume": 45000000,
    "change_percent": 2.5
  }
}
```

### GET /compare/{tickers}

Compare P/E ratios for multiple stocks.

**Example:** `GET /compare/NVDA,AMD,INTC`

**Response:**
```json
{
  "success": true,
  "comparison": [
    {"ticker": "NVDA", "pe_ratio": 65.2, "price": 875.50},
    {"ticker": "AMD", "pe_ratio": 45.8, "price": 178.20},
    {"ticker": "INTC", "pe_ratio": 22.1, "price": 42.30}
  ]
}
```

## Rate Limiting

Implemented with `slowapi`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze(request: Request, ...):
    ...
```

> **Note:** The first parameter must be `Request` for rate limiting to work.

## Pydantic Validation

Requests are automatically validated:

```python
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=1000)
    tickers: list[str] | None = Field(default=None, max_length=5)
```

## CORS

- **Dev:** `allow_origins=["*"]`
- **Prod:** CORS disabled (API-only, Telegram bot is internal)

## Running the Server

### Development

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker)

```bash
docker compose up -d
```

## API Documentation

Auto-generated Swagger UI available at:
- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)
- [slowapi](https://github.com/laurentS/slowapi)
- [prometheus-client](https://github.com/prometheus/client_python)

# FastAPI Backend

## Pourquoi FastAPI ?

FastAPI est le framework web pour exposer l'API de recherche financière.

### Avantages

| Critère | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| **Performance** | Async natif | Sync | Sync |
| **Typage** | Pydantic natif | Manuel | Manuel |
| **OpenAPI** | Auto-généré | Manuel | DRF |
| **Validation** | Automatique | Manuel | Serializers |

### Raisons du choix

1. **Async natif** : Parfait pour I/O-bound (API calls, DB)
2. **Pydantic** : Validation + serialization automatiques
3. **OpenAPI** : Documentation Swagger auto-générée
4. **Performance** : Un des frameworks Python les plus rapides

## Architecture

```
src/api/
└── main.py
    ├── GET  /health           # Health check
    ├── POST /analyze          # Lancer une analyse
    ├── GET  /quote/{ticker}   # Quote temps réel
    └── GET  /compare/{tickers}# Comparer P/E ratios
```

## Endpoints

### GET /health

Health check pour monitoring.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production"
}
```

### POST /analyze

Lance une recherche d'analyse financière.

**Request:**
```json
{
  "query": "Analyze NVDA and check their 10-K for China supply chain risks",
  "tickers": ["NVDA"]
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `query` | string | Requête de recherche (10-1000 chars) |
| `tickers` | string[] | Optionnel, max 5 tickers (auto-détecté sinon) |

**Response:**
```json
{
  "success": true,
  "report": {
    "summary": "...",
    "analysis": "..."
  },
  "market_data": {
    "NVDA": {...}
  },
  "errors": []
}
```

**Rate limit:** 10/minute

### GET /quote/{ticker}

Récupère un quote temps réel pour un ticker.

**Example:** `GET /quote/NVDA`

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "NVDA",
    "price": 875.50,
    "pe_ratio": 65.2,
    "market_cap": 2150000000000,
    "volume": 45000000
  }
}
```

**Rate limit:** 30/minute

### GET /compare/{tickers}

Compare les P/E ratios de plusieurs actions.

**Example:** `GET /compare/NVDA,AMD,INTC`

**Response:**
```json
{
  "success": true,
  "comparison": {
    "NVDA": {"pe_ratio": 65.2, "price": 875.50},
    "AMD": {"pe_ratio": 45.8, "price": 178.20},
    "INTC": {"pe_ratio": 22.1, "price": 42.30}
  }
}
```

**Rate limit:** 20/minute (max 5 tickers)

## Rate Limiting

Implémenté avec `slowapi` pour éviter les abus :

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze(request: Request, analysis_request: AnalyzeRequest):
    ...
```

> **Note:** Depuis slowapi, le premier paramètre doit être `Request` pour que le rate limiting fonctionne.

## Validation Pydantic

Les requêtes sont validées automatiquement :

```python
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=1000)
    tickers: list[str] | None = Field(default=None, max_length=5)
```

## CORS

- **Dev:** `allow_origins=["*"]`
- **Prod:** CORS désactivé (API-only)

## Lancer le serveur

### Development

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker)

```bash
docker-compose up app
```

## Documentation API

Swagger UI auto-généré disponible sur :
- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Live:** https://equity-research-agent.wonderfulstone-1de7f015.swedencentral.azurecontainerapps.io/docs

## Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)
- [slowapi](https://github.com/laurentS/slowapi)

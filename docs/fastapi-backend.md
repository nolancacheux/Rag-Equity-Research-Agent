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
    ├── /health          # Health check
    ├── /research        # Lancer une recherche
    └── /research/{id}   # Récupérer résultats
```

## Endpoints

### POST /research

Lance une recherche asynchrone.

**Request:**
```json
{
  "query": "Analyze NVDA and check their 10-K for China supply chain risks",
  "tickers": ["NVDA"]  // Optionnel
}
```

**Response:**
```json
{
  "research_id": "uuid",
  "status": "processing",
  "tickers": ["NVDA"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /research/{research_id}

Récupère les résultats d'une recherche.

**Response:**
```json
{
  "research_id": "uuid",
  "status": "completed",
  "report": {
    "summary": "...",
    "market_data": {...},
    "document_analysis": [...],
    "news_sentiment": {...}
  }
}
```

### GET /health

Health check pour monitoring.

**Response:**
```json
{
  "status": "healthy",
  "qdrant": "connected",
  "redis": "connected"
}
```

## Rate Limiting

Implémenté avec `slowapi` pour éviter les abus :

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/research")
@limiter.limit("100/minute")
async def create_research(request: ResearchRequest):
    ...
```

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_REQUESTS` | Requêtes max | `100` |
| `RATE_LIMIT_PERIOD` | Période (sec) | `60` |

## Validation Pydantic

Les requêtes sont validées automatiquement :

```python
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=1000)
    tickers: list[str] | None = Field(default=None, max_length=5)
```

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

## Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)

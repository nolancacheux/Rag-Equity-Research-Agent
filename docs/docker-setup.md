# Docker Setup

## Overview

The project uses Docker Compose to orchestrate multiple services:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│     API     │────▶│   Qdrant    │     │ Telegram    │
│  (FastAPI)  │     │  (Vectors)  │     │    Bot      │
│   :8000     │     │ :6333/:6334 │     │  (polling)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Services

### api (FastAPI)

Main application with REST API.

```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile.api
  ports:
    - "8000:8000"
  environment:
    - GROQ_API_KEY=${GROQ_API_KEY}
    - QDRANT_URL=http://qdrant:6333
    - API_SECRET_KEY=${API_SECRET_KEY}
  depends_on:
    - qdrant
```

### telegram-bot

Telegram bot service (optional).

```yaml
telegram-bot:
  build:
    context: .
    dockerfile: Dockerfile.bot
  environment:
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - API_BASE_URL=http://api:8000
    - API_SECRET_KEY=${API_SECRET_KEY}
  depends_on:
    - api
```

### qdrant (Vector Database)

Vector database for RAG.

```yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"  # REST API
    - "6334:6334"  # gRPC
  volumes:
    - qdrant_data:/qdrant/storage
```

## Commands

### Start All Services

```bash
docker compose up -d
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
```

### Stop

```bash
docker compose down

# With volume deletion (reset data)
docker compose down -v
```

### Rebuild After Changes

```bash
docker compose up -d --build api
```

## Dockerfiles

### Dockerfile.api

Lightweight API image (~500MB):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install deps (no PyTorch)
RUN pip install --no-cache-dir \
    langchain langgraph fastapi uvicorn ...

COPY src/ src/

USER appuser
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.bot

Telegram bot image:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    python-telegram-bot httpx pydantic ...

COPY src/ src/

USER appuser
CMD ["python", "-m", "src.telegram.bot"]
```

## Volumes

| Volume | Service | Contents |
|--------|---------|----------|
| `qdrant_data` | qdrant | Vector collections |

### Backup Data

```bash
# Qdrant
docker cp equity-research-agent-qdrant-1:/qdrant/storage ./backup/qdrant
```

## Environment Variables

Create a `.env` file:

```env
# LLM Provider (at least one required)
GROQ_API_KEY=gsk_...        # FREE
OPENAI_API_KEY=sk-...       # Paid

# API Security (production)
API_SECRET_KEY=your-generated-key

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=123456789:ABC...

# Monitoring (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_xxx
```

## Production Configuration

For production, add:

1. **Health checks** in docker-compose
2. **Resource limits** (CPU, memory)
3. **Restart policies**
4. **Logging driver** (json-file, syslog, etc.)

```yaml
api:
  ...
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  restart: unless-stopped
```

## Caching

The API uses an in-memory cache with TTL for API responses. This provides:
- Fast response times for repeated queries
- No external dependencies
- Automatic cleanup of expired entries

For high-traffic production deployments, consider adding Redis or Memcached.

## Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Qdrant Docker](https://qdrant.tech/documentation/quick-start/)

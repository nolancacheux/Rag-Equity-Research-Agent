# Docker Setup

## Vue d'ensemble

Le projet utilise Docker Compose pour orchestrer 3 services :

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│     App     │────▶│   Qdrant    │     │    Redis    │
│  (FastAPI)  │     │  (Vectors)  │     │   (Cache)   │
│   :8000     │     │ :6333/:6334 │     │    :6379    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Services

### app (FastAPI)

L'application principale.

```yaml
app:
  build:
    context: .
    dockerfile: Dockerfile
  ports:
    - "8000:8000"
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - QDRANT_URL=http://qdrant:6333
    - REDIS_URL=redis://redis:6379
  depends_on:
    - qdrant
    - redis
```

### qdrant (Vector Database)

Base de données vectorielle pour le RAG.

```yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"  # REST API
    - "6334:6334"  # gRPC
  volumes:
    - qdrant_data:/qdrant/storage
```

### redis (Cache)

Cache pour les réponses API.

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
```

## Commandes

### Démarrer tous les services

```bash
docker-compose up -d
```

### Logs

```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f app
```

### Arrêter

```bash
docker-compose down

# Avec suppression des volumes (reset data)
docker-compose down -v
```

### Rebuild après changement

```bash
docker-compose up -d --build app
```

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source
COPY src/ src/

# Run
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Volumes

| Volume | Service | Contenu |
|--------|---------|---------|
| `qdrant_data` | qdrant | Collections vectorielles |
| `redis_data` | redis | Cache persisté (AOF) |

### Backup des données

```bash
# Qdrant
docker cp equity-research-agent-qdrant-1:/qdrant/storage ./backup/qdrant

# Redis
docker cp equity-research-agent-redis-1:/data ./backup/redis
```

## Variables d'environnement

Créer un fichier `.env` :

```env
# Required
OPENAI_API_KEY=sk-xxx

# Optional (LangSmith tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_xxx
LANGCHAIN_PROJECT=equity-research-agent

# Optional (Qdrant Cloud)
QDRANT_API_KEY=xxx
```

## Production

Pour la production, ajouter :

1. **Health checks** dans docker-compose
2. **Resource limits** (CPU, memory)
3. **Restart policies**
4. **Logging driver** (json-file, syslog, etc.)

```yaml
app:
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
```

## Ressources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Qdrant Docker](https://qdrant.tech/documentation/quick-start/)
- [Redis Docker](https://hub.docker.com/_/redis)

# Documentation

Documentation technique du projet Equity Research Agent.

## Index

| Document | Description |
|----------|-------------|
| [azure-deployment.md](./azure-deployment.md) | Deployment Azure (Container Apps, OpenAI) |
| [terraform/](../terraform/README.md) | Infrastructure as Code (recommended) |
| [qdrant-vector-database.md](./qdrant-vector-database.md) | Base de données vectorielle pour le RAG |
| [langgraph-orchestration.md](./langgraph-orchestration.md) | Orchestration des agents avec LangGraph |
| [redis-caching.md](./redis-caching.md) | Caching Redis pour les API calls |
| [embeddings-rag.md](./embeddings-rag.md) | Pipeline RAG et modèle d'embeddings |
| [fastapi-backend.md](./fastapi-backend.md) | API REST FastAPI |
| [docker-setup.md](./docker-setup.md) | Configuration Docker Compose |
| [financial-data-tools.md](./financial-data-tools.md) | Sources de données (yfinance, SEC, DuckDuckGo) |

## Structure du projet

```
equity-research-agent/
├── src/
│   ├── agents/          # Agents LangGraph
│   ├── api/             # FastAPI endpoints
│   ├── config/          # Configuration Pydantic
│   ├── rag/             # RAG pipeline (embeddings, chunking, vector store)
│   ├── tools/           # Data fetching tools
│   └── utils/           # Utilities (cache, rate limiter)
├── terraform/           # Infrastructure as Code (Azure)
├── tests/               # Tests unitaires
├── docs/                # Cette documentation
├── docker-compose.yml   # Orchestration services
├── Dockerfile           # Image de l'app
└── pyproject.toml       # Dependencies & config
```

## Quick Start

```bash
# 1. Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec votre OPENAI_API_KEY

# 2. Lancer les services
docker-compose up -d

# 3. Tester l'API
curl http://localhost:8000/health
```

## Contribution

Lors de l'ajout d'un nouveau composant :
1. Créer la documentation dans `docs/`
2. Mettre à jour cet index
3. Documenter le "pourquoi" (choix techniques) autant que le "comment"

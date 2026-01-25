# Qdrant Vector Database

## Pourquoi Qdrant ?

Qdrant est utilisé comme base de données vectorielle pour le stockage et la recherche sémantique des documents financiers (SEC filings, rapports annuels, etc.).

### Avantages par rapport aux alternatives

| Critère | Qdrant | Pinecone | Chroma |
|---------|--------|----------|--------|
| **Self-hosted** | Oui | Non (SaaS) | Oui |
| **Performance** | Excellent | Excellent | Moyen |
| **Filtrage** | Natif et rapide | Bon | Limité |
| **Coût** | Gratuit (self-hosted) | Payant | Gratuit |
| **Production-ready** | Oui | Oui | Non recommandé |

### Raisons du choix

1. **Self-hosted** : Pas de dépendance SaaS, contrôle total des données financières sensibles
2. **Filtrage puissant** : Filtrage par ticker, type de document (10-K, 10-Q), date
3. **Performance** : Recherche HNSW optimisée pour la similarité cosinus
4. **Docker-native** : S'intègre parfaitement dans notre stack Docker Compose

## Architecture dans le projet

```
src/rag/vector_store.py
└── QdrantStore
    ├── add_chunks()      # Indexation des documents
    ├── search()          # Recherche sémantique générique
    ├── search_sec_filing() # Recherche dans un filing spécifique
    └── delete_by_ticker() # Suppression par ticker
```

## Configuration

### Docker Compose

```yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"  # REST API
    - "6334:6334"  # gRPC
  volumes:
    - qdrant_data:/qdrant/storage
```

### Variables d'environnement

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_URL` | URL du serveur Qdrant | `http://localhost:6333` |
| `QDRANT_API_KEY` | Clé API (optionnel en dev) | `None` |
| `QDRANT_COLLECTION` | Nom de la collection | `sec_filings` |

## Utilisation

### Indexation de documents

```python
from src.rag.vector_store import QdrantStore
from src.rag.chunking import chunk_document

store = QdrantStore()

# Chunker un document et l'indexer
chunks = chunk_document(document_text, metadata={"ticker": "NVDA", "form_type": "10-K"})
store.add_chunks(chunks)
```

### Recherche sémantique

```python
# Recherche générique
results = store.search(
    query="China supply chain risks",
    top_k=5,
    score_threshold=0.5
)

# Recherche dans un filing spécifique
results = store.search_sec_filing(
    query="revenue growth drivers",
    ticker="NVDA",
    form_type="10-K"
)
```

## Schema des données

Chaque point dans Qdrant contient :

```json
{
  "id": "uuid",
  "vector": [0.1, 0.2, ...],  // 384 dimensions (MiniLM)
  "payload": {
    "content": "Texte du chunk",
    "chunk_index": 0,
    "start_char": 0,
    "end_char": 500,
    "ticker": "NVDA",
    "form_type": "10-K",
    "filing_date": "2024-01-15",
    "source": "sec_edgar"
  }
}
```

## Maintenance

### Stats de la collection

```python
stats = store.get_stats()
# {"collection": "sec_filings", "vectors_count": 15000, "points_count": 15000, "status": "green"}
```

### Suppression par ticker

```python
store.delete_by_ticker("NVDA")  # Supprime tous les docs NVDA
```

## Ressources

- [Documentation Qdrant](https://qdrant.tech/documentation/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)

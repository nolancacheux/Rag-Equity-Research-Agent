# Embeddings & RAG Pipeline

## Vue d'ensemble

Le pipeline RAG (Retrieval-Augmented Generation) permet de chercher dans les SEC filings et autres documents pour répondre aux questions financières.

```
Document → Chunking → Embeddings → Qdrant → Search → LLM Synthesis
```

## Modèle d'embeddings

### Azure OpenAI text-embedding-ada-002

| Propriété | Valeur |
|-----------|--------|
| **Dimension** | 1536 |
| **Provider** | Azure OpenAI |
| **Max tokens** | 8191 |
| **Qualité** | Production-ready, excellent semantic search |

### Pourquoi Azure OpenAI ?

1. **Production-ready** : API stable et scalable
2. **Crédits Azure** : Utilisation des crédits gratuits Azure for Students
3. **Pas de PyTorch** : Image Docker légère (~500MB vs 2GB+)
4. **Cold start rapide** : Pas de chargement de modèle local
5. **Maintenance réduite** : Pas de gestion de modèles ML

## Configuration

### Variables d'environnement

```bash
# Azure OpenAI (requis)
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-02-01
```

## Architecture

```
src/rag/
├── embeddings.py   # EmbeddingService (Azure OpenAI)
├── chunking.py     # Document chunking
└── vector_store.py # Qdrant integration
```

### EmbeddingService

```python
from src.rag.embeddings import get_embedding_service

embeddings = get_embedding_service()

# Single text
vector = embeddings.embed("NVIDIA revenue growth")  # → [0.1, 0.2, ...] (1536 dims)

# Batch (plus efficace)
vectors = embeddings.embed_batch(["text1", "text2", "text3"])
```

### Propriétés

```python
embeddings.dimension  # 1536
```

## Chunking Strategy

Les documents longs sont découpés en chunks pour :
1. Respecter les limites de context window
2. Améliorer la précision de la recherche
3. Permettre des citations précises

### Paramètres

| Paramètre | Valeur | Raison |
|-----------|--------|--------|
| `chunk_size` | 500 chars | Balance précision/contexte |
| `chunk_overlap` | 50 chars | Évite de couper des phrases |

### DocumentChunk

```python
@dataclass
class DocumentChunk:
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict[str, Any]
```

## Pipeline complet

### 1. Ingestion d'un SEC filing

```python
from src.rag.chunking import chunk_document
from src.rag.vector_store import QdrantStore

# Télécharger le 10-K
filing_text = download_sec_filing("NVDA", "10-K")

# Chunker
chunks = chunk_document(
    text=filing_text,
    metadata={
        "ticker": "NVDA",
        "form_type": "10-K",
        "filing_date": "2024-01-15"
    }
)

# Indexer dans Qdrant
store = QdrantStore()
store.add_chunks(chunks)  # Embeddings générés via Azure OpenAI
```

### 2. Recherche

```python
results = store.search_sec_filing(
    query="What are the main risks related to China?",
    ticker="NVDA",
    form_type="10-K",
    top_k=5
)

for r in results:
    print(f"Score: {r['score']:.2f}")
    print(f"Content: {r['content'][:200]}...")
```

## Performance

### Batch processing

Pour l'indexation de gros documents :

```python
store.add_chunks(chunks, batch_size=16)  # Azure max batch = 16
```

### Rate limiting

Azure OpenAI a des limites de rate :
- 10 requests / 10 seconds
- 10,000 tokens / minute

Le service gère automatiquement les batches pour respecter ces limites.

## Migration depuis sentence-transformers

Si vous aviez des embeddings en 384 dimensions (all-MiniLM-L6-v2), vous devez :
1. Recréer la collection Qdrant avec dimension=1536
2. Ré-indexer tous les documents

```python
# Mise à jour de la collection Qdrant
store = QdrantStore()
store.recreate_collection(vector_size=1536)
```

## Ressources

- [Azure OpenAI Embeddings](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/understand-embeddings)
- [text-embedding-ada-002](https://platform.openai.com/docs/guides/embeddings)

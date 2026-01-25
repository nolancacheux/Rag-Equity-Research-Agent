# Embeddings & RAG Pipeline

## Vue d'ensemble

Le pipeline RAG (Retrieval-Augmented Generation) permet de chercher dans les SEC filings et autres documents pour répondre aux questions financières.

```
Document → Chunking → Embeddings → Qdrant → Search → LLM Synthesis
```

## Modèle d'embeddings

### all-MiniLM-L6-v2

| Propriété | Valeur |
|-----------|--------|
| **Dimension** | 384 |
| **Taille** | 80 MB |
| **Vitesse** | ~14,000 sentences/sec (GPU) |
| **Qualité** | Excellent pour semantic search |

### Pourquoi ce modèle ?

1. **Léger** : Tourne sur CPU sans problème
2. **Rapide** : Batch processing efficace
3. **Qualité** : Top performance sur benchmarks semantic similarity
4. **Gratuit** : Pas d'API payante (vs OpenAI embeddings)

## Architecture

```
src/rag/
├── embeddings.py   # EmbeddingService (sentence-transformers)
├── chunking.py     # Document chunking
└── vector_store.py # Qdrant integration
```

### EmbeddingService

```python
from src.rag.embeddings import get_embedding_service

embeddings = get_embedding_service()

# Single text
vector = embeddings.embed("NVIDIA revenue growth")  # → [0.1, 0.2, ...]

# Batch (plus efficace)
vectors = embeddings.embed_batch(["text1", "text2", "text3"])
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
store.add_chunks(chunks)  # Embeddings générés automatiquement
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
store.add_chunks(chunks, batch_size=100)  # Embeddings en batch de 100
```

### Lazy loading

Le modèle est chargé uniquement au premier appel :

```python
embeddings = get_embedding_service()  # Pas de chargement
embeddings.embed("test")  # Chargement ici (une seule fois)
```

## Ressources

- [Sentence Transformers](https://www.sbert.net/)
- [all-MiniLM-L6-v2 Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

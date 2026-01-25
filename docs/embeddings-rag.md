# Embeddings & RAG Pipeline

## Overview

The RAG (Retrieval-Augmented Generation) pipeline enables searching through SEC filings and other documents to answer financial questions.

```
Document → Chunking → Embeddings → Qdrant → Search → LLM Synthesis
```

## Embedding Model

### Azure OpenAI text-embedding-ada-002

| Property | Value |
|----------|-------|
| **Dimension** | 1536 |
| **Provider** | Azure OpenAI |
| **Max tokens** | 8191 |
| **Quality** | Production-ready, excellent semantic search |

### Why Azure OpenAI?

1. **Production-ready**: Stable and scalable API
2. **Azure credits**: Use free Azure for Students credits
3. **No PyTorch**: Lightweight Docker image (~500MB vs 2GB+)
4. **Fast cold start**: No local model loading
5. **Reduced maintenance**: No ML model management

## Configuration

### Environment Variables

```bash
# Azure OpenAI (required)
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

# Batch (more efficient)
vectors = embeddings.embed_batch(["text1", "text2", "text3"])
```

### Properties

```python
embeddings.dimension  # 1536
```

## Chunking Strategy

Long documents are split into chunks to:
1. Respect context window limits
2. Improve search precision
3. Enable precise citations

### Parameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| `chunk_size` | 500 chars | Balance precision/context |
| `chunk_overlap` | 50 chars | Avoid cutting sentences |

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

## Full Pipeline

### 1. Ingesting a SEC Filing

```python
from src.rag.chunking import chunk_document
from src.rag.vector_store import QdrantStore

# Download the 10-K
filing_text = download_sec_filing("NVDA", "10-K")

# Chunk it
chunks = chunk_document(
    text=filing_text,
    metadata={
        "ticker": "NVDA",
        "form_type": "10-K",
        "filing_date": "2024-01-15"
    }
)

# Index in Qdrant
store = QdrantStore()
store.add_chunks(chunks)  # Embeddings generated via Azure OpenAI
```

### 2. Search

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

### Batch Processing

For indexing large documents:

```python
store.add_chunks(chunks, batch_size=16)  # Azure max batch = 16
```

### Rate Limiting

Azure OpenAI has rate limits:
- 10 requests / 10 seconds
- 10,000 tokens / minute

The service automatically handles batching to respect these limits.

## Migration from sentence-transformers

If you had embeddings in 384 dimensions (all-MiniLM-L6-v2), you need to:
1. Recreate the Qdrant collection with dimension=1536
2. Re-index all documents

```python
# Update Qdrant collection
store = QdrantStore()
store.recreate_collection(vector_size=1536)
```

## Resources

- [Azure OpenAI Embeddings](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/understand-embeddings)
- [text-embedding-ada-002](https://platform.openai.com/docs/guides/embeddings)

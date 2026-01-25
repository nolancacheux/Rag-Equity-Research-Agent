# Qdrant Vector Database

## Why Qdrant?

Qdrant is used as the vector database for storing and semantic searching of financial documents (SEC filings, annual reports, etc.).

### Advantages over Alternatives

| Criteria | Qdrant | Pinecone | Chroma |
|----------|--------|----------|--------|
| **Self-hosted** | Yes | No (SaaS) | Yes |
| **Performance** | Excellent | Excellent | Medium |
| **Filtering** | Native and fast | Good | Limited |
| **Cost** | Free (self-hosted) | Paid | Free |
| **Production-ready** | Yes | Yes | Not recommended |

### Reasons for Choice

1. **Self-hosted**: No SaaS dependency, full control over sensitive financial data
2. **Powerful filtering**: Filter by ticker, document type (10-K, 10-Q), date
3. **Performance**: HNSW search optimized for cosine similarity
4. **Docker-native**: Integrates perfectly into our Docker Compose stack

## Architecture in the Project

```
src/rag/vector_store.py
└── QdrantStore
    ├── add_chunks()        # Document indexing
    ├── search()            # Generic semantic search
    ├── search_sec_filing() # Search in a specific filing
    └── delete_by_ticker()  # Delete by ticker
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

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` |
| `QDRANT_API_KEY` | API key (optional in dev) | `None` |
| `QDRANT_COLLECTION` | Collection name | `sec_filings` |

## Usage

### Document Indexing

```python
from src.rag.vector_store import QdrantStore
from src.rag.chunking import chunk_document

store = QdrantStore()

# Chunk a document and index it
chunks = chunk_document(document_text, metadata={"ticker": "NVDA", "form_type": "10-K"})
store.add_chunks(chunks)
```

### Semantic Search

```python
# Generic search
results = store.search(
    query="China supply chain risks",
    top_k=5,
    score_threshold=0.5
)

# Search in a specific filing
results = store.search_sec_filing(
    query="revenue growth drivers",
    ticker="NVDA",
    form_type="10-K"
)
```

## Data Schema

Each point in Qdrant contains:

```json
{
  "id": "uuid",
  "vector": [0.1, 0.2, ...],  // 1536 dimensions (Azure OpenAI)
  "payload": {
    "content": "Chunk text",
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

### Collection Stats

```python
stats = store.get_stats()
# {"collection": "sec_filings", "vectors_count": 15000, "points_count": 15000, "status": "green"}
```

### Delete by Ticker

```python
store.delete_by_ticker("NVDA")  # Removes all NVDA docs
```

## Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)

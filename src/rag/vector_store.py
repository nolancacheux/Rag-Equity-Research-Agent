"""Qdrant vector store for semantic search."""

from typing import Any
from uuid import uuid4

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.config import get_settings
from src.rag.chunking import DocumentChunk
from src.rag.embeddings import EmbeddingService, get_embedding_service

logger = structlog.get_logger()


class QdrantStore:
    """Vector store using Qdrant for document retrieval.
    
    Supports:
    - Document indexing with metadata
    - Semantic similarity search
    - Filtered search (by ticker, form type, etc.)
    """

    def __init__(
        self,
        collection_name: str | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        """Initialize Qdrant store.
        
        Args:
            collection_name: Name of the Qdrant collection
            embedding_service: Optional embedding service instance
        """
        self._settings = get_settings()
        self._collection_name = collection_name or self._settings.qdrant_collection
        self._embeddings = embedding_service or get_embedding_service()
        self._client: QdrantClient | None = None

    def _get_client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            api_key = self._settings.qdrant_api_key
            self._client = QdrantClient(
                url=self._settings.qdrant_url,
                api_key=api_key.get_secret_value() if api_key else None,
            )
            logger.info("qdrant_connected", url=self._settings.qdrant_url)
        return self._client

    def _ensure_collection(self) -> None:
        """Ensure collection exists with proper schema."""
        client = self._get_client()
        
        try:
            client.get_collection(self._collection_name)
            logger.debug("collection_exists", name=self._collection_name)
        except (UnexpectedResponse, Exception):
            # Create collection
            client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=self._embeddings.dimension,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info("collection_created", name=self._collection_name)

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        batch_size: int = 100,
    ) -> int:
        """Add document chunks to the vector store.
        
        Args:
            chunks: List of DocumentChunk objects
            batch_size: Batch size for indexing
            
        Returns:
            Number of chunks indexed
        """
        if not chunks:
            return 0
        
        self._ensure_collection()
        client = self._get_client()
        
        # Generate embeddings in batches
        texts = [chunk.content for chunk in chunks]
        embeddings = self._embeddings.embed_batch(texts, batch_size=batch_size)
        
        # Create points
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid4())
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        **chunk.metadata,
                    },
                )
            )
        
        # Upsert in batches
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(
                collection_name=self._collection_name,
                points=batch,
            )
        
        logger.info("chunks_indexed", count=len(chunks))
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        score_threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filters (e.g., {"ticker": "NVDA"})
            score_threshold: Minimum similarity score
            
        Returns:
            List of matching documents with scores
        """
        self._ensure_collection()
        client = self._get_client()
        
        # Generate query embedding
        query_embedding = self._embeddings.embed(query)
        
        # Build filter conditions
        filter_conditions = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value),
                        )
                    )
                else:
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        )
                    )
            filter_conditions = models.Filter(must=conditions)
        
        # Search
        results = client.search(
            collection_name=self._collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=filter_conditions,
            score_threshold=score_threshold,
        )
        
        # Format results
        formatted = []
        for result in results:
            formatted.append({
                "content": result.payload.get("content", ""),
                "score": result.score,
                "metadata": {
                    k: v for k, v in result.payload.items() 
                    if k not in ["content"]
                },
            })
        
        logger.info("search_completed", query=query[:50], results=len(formatted))
        return formatted

    def search_sec_filing(
        self,
        query: str,
        ticker: str,
        form_type: str = "10-K",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search within a specific SEC filing.
        
        Args:
            query: Search query (e.g., "China supply chain risks")
            ticker: Stock ticker symbol
            form_type: SEC form type (10-K, 10-Q, etc.)
            top_k: Number of results
            
        Returns:
            List of relevant passages
        """
        return self.search(
            query=query,
            top_k=top_k,
            filters={
                "ticker": ticker.upper(),
                "form_type": form_type,
            },
        )

    def delete_by_ticker(self, ticker: str) -> bool:
        """Delete all documents for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            True if successful
        """
        client = self._get_client()
        
        try:
            client.delete(
                collection_name=self._collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="ticker",
                                match=models.MatchValue(value=ticker.upper()),
                            )
                        ]
                    )
                ),
            )
            logger.info("documents_deleted", ticker=ticker)
            return True
        except Exception as e:
            logger.error("delete_failed", ticker=ticker, error=str(e))
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Collection statistics
        """
        client = self._get_client()
        
        try:
            info = client.get_collection(self._collection_name)
            return {
                "collection": self._collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception as e:
            logger.error("stats_failed", error=str(e))
            return {"error": str(e)}

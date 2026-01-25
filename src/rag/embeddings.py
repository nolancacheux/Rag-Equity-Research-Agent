"""Embedding service for vector representations using Azure OpenAI."""

from functools import lru_cache

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating text embeddings using Azure OpenAI.
    
    Uses Azure OpenAI text-embedding-ada-002 for production-ready embeddings.
    Dimension: 1536
    """

    DIMENSION = 1536  # text-embedding-ada-002 dimension

    def __init__(self) -> None:
        """Initialize embedding service with Azure OpenAI."""
        settings = get_settings()
        
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise ValueError("Azure OpenAI credentials required for embeddings")
        
        self._endpoint = settings.azure_openai_endpoint.rstrip("/")
        self._api_key = settings.azure_openai_api_key.get_secret_value()
        self._deployment = settings.azure_openai_embedding_deployment
        self._api_version = settings.azure_openai_api_version
        
        logger.info(
            "embedding_service_initialized",
            endpoint=self._endpoint,
            deployment=self._deployment,
        )

    def _get_url(self) -> str:
        """Build Azure OpenAI embeddings API URL."""
        return (
            f"{self._endpoint}/openai/deployments/{self._deployment}"
            f"/embeddings?api-version={self._api_version}"
        )

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats (1536 dimensions)
        """
        embeddings = self.embed_batch([text])
        return embeddings[0] if embeddings else []

    def embed_batch(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for API calls (max 16 for Azure)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings: list[list[float]] = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = httpx.post(
                self._get_url(),
                headers={
                    "api-key": self._api_key,
                    "Content-Type": "application/json",
                },
                json={"input": batch},
                timeout=30.0,
            )
            response.raise_for_status()
            
            data = response.json()
            batch_embeddings = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(batch_embeddings)
        
        logger.debug("batch_embedded", count=len(texts))
        return all_embeddings

    @property
    def dimension(self) -> int:
        """Get embedding dimension (1536 for ada-002)."""
        return self.DIMENSION


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service instance."""
    return EmbeddingService()

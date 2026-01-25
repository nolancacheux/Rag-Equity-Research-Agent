"""Embedding service for vector representations."""

from functools import lru_cache

import structlog
from sentence_transformers import SentenceTransformer

from src.config import get_settings

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating text embeddings.
    
    Uses sentence-transformers for local embeddings.
    Supports batched processing for efficiency.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str | None = None) -> None:
        """Initialize embedding service.
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
        """
        self._model_name = model_name or self.DEFAULT_MODEL
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            logger.info("loading_embedding_model", model=self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("embedding_model_loaded", model=self._model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        model = self._load_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        
        logger.debug("batch_embedded", count=len(texts))
        return [e.tolist() for e in embeddings]

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        model = self._load_model()
        return model.get_sentence_embedding_dimension()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service instance."""
    return EmbeddingService()

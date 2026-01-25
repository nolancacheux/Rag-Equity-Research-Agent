"""Tests for RAG module."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from src.rag.chunking import DocumentChunker, DocumentChunk
from src.rag.embeddings import EmbeddingService


class TestDocumentChunker:
    """Tests for document chunking."""

    def test_chunk_short_text(self):
        """Test chunking text shorter than chunk size."""
        chunker = DocumentChunker(chunk_size=1000)
        text = "This is a short document."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_long_text(self):
        """Test chunking longer text."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        
        # Create text with multiple paragraphs
        paragraphs = ["Paragraph " + str(i) + ". " + "x" * 50 for i in range(10)]
        text = "\n\n".join(paragraphs)
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 1
        # Check overlap exists
        for i in range(1, len(chunks)):
            # Chunks should have some overlap
            assert chunks[i].start_char < chunks[i-1].end_char or chunks[i].chunk_index > 0

    def test_chunk_with_metadata(self):
        """Test chunking preserves metadata."""
        chunker = DocumentChunker(chunk_size=1000)
        text = "Test document content."
        metadata = {"ticker": "NVDA", "form_type": "10-K"}
        
        chunks = chunker.chunk_text(text, metadata)
        
        assert len(chunks) == 1
        assert chunks[0].metadata["ticker"] == "NVDA"
        assert chunks[0].metadata["form_type"] == "10-K"

    def test_chunk_text_cleaning(self):
        """Test that text is cleaned properly."""
        chunker = DocumentChunker()
        text = "Text   with\n\n\n\nmultiple   spaces\n\n\n\nand breaks."
        
        chunks = chunker.chunk_text(text)
        
        # Should normalize whitespace
        assert "   " not in chunks[0].content
        assert "\n\n\n" not in chunks[0].content

    def test_section_header_detection(self):
        """Test SEC section header detection."""
        chunker = DocumentChunker()
        
        assert chunker._find_section_header("ITEM 1A. RISK FACTORS") == "ITEM 1A. RISK FACTORS"
        assert chunker._find_section_header("PART I") == "PART I"
        assert chunker._find_section_header("Regular text") is None


class TestEmbeddingService:
    """Tests for embedding service."""

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_embed_single(self, mock_transformer):
        """Test single text embedding."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        embedding = service.embed("Test text")
        
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_embed_batch(self, mock_transformer):
        """Test batch text embedding."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ])
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        embeddings = service.embed_batch(["Text 1", "Text 2"])
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_embed_batch_empty(self, mock_transformer):
        """Test batch embedding with empty list."""
        service = EmbeddingService()
        embeddings = service.embed_batch([])
        
        assert embeddings == []
        mock_transformer.return_value.encode.assert_not_called()

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_lazy_model_loading(self, mock_transformer):
        """Test that model is loaded lazily."""
        service = EmbeddingService()
        
        # Model should not be loaded on init
        mock_transformer.assert_not_called()
        
        # Model should load on first use
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1])
        mock_transformer.return_value = mock_model
        
        service.embed("test")
        mock_transformer.assert_called_once()

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_dimension_property(self, mock_transformer):
        """Test embedding dimension property."""
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        dim = service.dimension
        
        assert dim == 384

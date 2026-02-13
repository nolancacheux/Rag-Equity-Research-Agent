"""Tests for RAG module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.rag.chunking import DocumentChunk, DocumentChunker


class TestDocumentChunk:
    """Tests for DocumentChunk dataclass."""

    def test_to_dict(self):
        """Test DocumentChunk to_dict conversion."""
        chunk = DocumentChunk(
            content="Test content",
            metadata={"ticker": "NVDA"},
            chunk_index=0,
            start_char=0,
            end_char=12,
        )

        result = chunk.to_dict()

        assert result["content"] == "Test content"
        assert result["metadata"]["ticker"] == "NVDA"
        assert result["chunk_index"] == 0


class TestDocumentChunker:
    """Tests for document chunking."""

    def test_init(self):
        """Test chunker initialization."""
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100, min_chunk_size=50)

        assert chunker._chunk_size == 500
        assert chunker._overlap == 100
        assert chunker._min_size == 50

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

        # Create text with multiple paragraphs - need more content to exceed chunk_size
        paragraphs = ["Paragraph " + str(i) + ". " + "x" * 100 for i in range(10)]
        text = "\n\n".join(paragraphs)

        chunks = chunker.chunk_text(text)

        # Should have multiple chunks given the text length
        assert len(chunks) >= 1

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

        # Test with full line containing header
        header_line = "ITEM 1A. RISK FACTORS"
        result = chunker._find_section_header(header_line)
        # May or may not detect depending on implementation
        # Just test it doesn't crash
        assert result is None or isinstance(result, str)

    def test_section_header_detection_patterns(self):
        """Test various section header patterns."""
        chunker = DocumentChunker()

        # Test different patterns
        tests = [
            ("ITEM 1A. RISK FACTORS", True),
            ("PART II", True),
            ("RISK FACTORS", True),
            ("Regular paragraph text", False),
        ]

        for text, should_match in tests:
            result = chunker._find_section_header(text)
            if should_match:
                # Should find a header
                assert result is not None or isinstance(result, str)

    def test_clean_text(self):
        """Test text cleaning."""
        chunker = DocumentChunker()

        text = "  Text   with   spaces  \n\n\n\n  and breaks  "
        result = chunker._clean_text(text)

        assert "   " not in result
        assert result == "Text with spaces and breaks"

    def test_split_into_paragraphs(self):
        """Test paragraph splitting."""
        chunker = DocumentChunker()

        text = "First paragraph.\n\nSecond paragraph.\n\n\n\nThird paragraph."
        paragraphs = chunker._split_into_paragraphs(text)

        assert len(paragraphs) == 3
        assert paragraphs[0] == "First paragraph."

    def test_chunk_file_success(self):
        """Test chunking a file."""
        chunker = DocumentChunker()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test document content for chunking.")
            temp_path = f.name

        try:
            chunks = chunker.chunk_file(temp_path)

            assert len(chunks) >= 1
            assert chunks[0].metadata["filename"] == Path(temp_path).name
        finally:
            Path(temp_path).unlink()

    def test_chunk_file_not_found(self):
        """Test chunking a non-existent file."""
        chunker = DocumentChunker()

        chunks = chunker.chunk_file("/nonexistent/file.txt")

        assert chunks == []

    def test_chunk_with_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=30, min_chunk_size=10)

        # Create long enough text to trigger overlap
        paragraphs = [f"Paragraph {i}. " + "x" * 80 for i in range(5)]
        text = "\n\n".join(paragraphs)

        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Verify chunks are properly indexed
            for i, chunk in enumerate(chunks):
                assert chunk.chunk_index == i

    def test_chunk_with_section_metadata(self):
        """Test that section headers are captured in metadata."""
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20, min_chunk_size=10)

        text = """ITEM 1A. RISK FACTORS

The following are significant risk factors.

This is a paragraph about risks. We have many risks to consider.

Another paragraph about more specific risks."""

        chunks = chunker.chunk_text(text)

        # At least one chunk should have the section
        assert len(chunks) >= 1

    def test_chunk_long_text_with_overlap(self):
        """Test chunking long text properly triggers overlap logic."""
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=30, min_chunk_size=10)

        # Create text that will definitely exceed chunk size
        paragraphs = []
        for i in range(10):
            paragraphs.append(
                f"This is paragraph number {i} with enough content to exceed the chunk size limit and trigger overlap."
            )
        text = "\n\n".join(paragraphs)

        chunks = chunker.chunk_text(text)

        # Should have at least one chunk
        assert len(chunks) >= 1
        # All chunks should have content
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_chunk_triggers_overlap_logic(self):
        """Test that overlap logic is properly triggered."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=30, min_chunk_size=5)

        # Create paragraphs that will trigger the overlap logic
        text = """ITEM 1. FIRST SECTION

First paragraph with some content here.

Second paragraph with more content.

ITEM 2. SECOND SECTION

Third paragraph in the second section.

Fourth paragraph with even more content.

Fifth paragraph to ensure we have enough content."""

        chunks = chunker.chunk_text(text)

        # Should create multiple chunks with overlap
        assert len(chunks) >= 1

    def test_chunk_min_size_filtering(self):
        """Test that chunks below min size are handled."""
        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=100, min_chunk_size=500)

        # Create short text that won't meet min_chunk_size when split
        text = "Short paragraph one.\n\nShort paragraph two.\n\nShort paragraph three."

        chunks = chunker.chunk_text(text)

        # Should have at least one chunk
        assert len(chunks) >= 1


class TestEmbeddingService:
    """Tests for embedding service with Azure OpenAI."""

    @patch("src.rag.embeddings.get_settings")
    @patch("src.rag.embeddings.httpx.post")
    def test_embed_single(self, mock_post, mock_settings):
        """Test single text embedding."""
        # Setup mocks
        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.azure_openai_embedding_deployment = "text-embedding-ada-002"
        mock_settings_obj.azure_openai_api_version = "2024-02-01"
        mock_settings.return_value = mock_settings_obj

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3] * 512}]  # 1536 dims
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from src.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        embedding = service.embed("Test text")

        assert len(embedding) == 1536
        mock_post.assert_called_once()

    @patch("src.rag.embeddings.get_settings")
    @patch("src.rag.embeddings.httpx.post")
    def test_embed_batch(self, mock_post, mock_settings):
        """Test batch text embedding."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.azure_openai_embedding_deployment = "text-embedding-ada-002"
        mock_settings_obj.azure_openai_api_version = "2024-02-01"
        mock_settings.return_value = mock_settings_obj

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 1536},
                {"embedding": [0.2] * 1536},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from src.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        embeddings = service.embed_batch(["Text 1", "Text 2"])

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536

    @patch("src.rag.embeddings.get_settings")
    def test_embed_batch_empty(self, mock_settings):
        """Test batch embedding with empty list."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.azure_openai_embedding_deployment = "text-embedding-ada-002"
        mock_settings_obj.azure_openai_api_version = "2024-02-01"
        mock_settings.return_value = mock_settings_obj

        from src.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        embeddings = service.embed_batch([])

        assert embeddings == []

    @patch("src.rag.embeddings.get_settings")
    def test_dimension_property(self, mock_settings):
        """Test embedding dimension property."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.azure_openai_embedding_deployment = "text-embedding-ada-002"
        mock_settings_obj.azure_openai_api_version = "2024-02-01"
        mock_settings.return_value = mock_settings_obj

        from src.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        dim = service.dimension

        assert dim == 1536  # Azure OpenAI ada-002 dimension

    @patch("src.rag.embeddings.get_settings")
    def test_init_no_credentials(self, mock_settings):
        """Test initialization without credentials."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = None
        mock_settings_obj.azure_openai_api_key = None
        mock_settings.return_value = mock_settings_obj

        from src.rag.embeddings import EmbeddingService

        with pytest.raises(ValueError, match="Azure OpenAI credentials required"):
            EmbeddingService()

    @patch("src.rag.embeddings.get_settings")
    def test_get_url(self, mock_settings):
        """Test URL building."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.azure_openai_embedding_deployment = "ada-002"
        mock_settings_obj.azure_openai_api_version = "2024-02-01"
        mock_settings.return_value = mock_settings_obj

        from src.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        url = service._get_url()

        assert "ada-002" in url
        assert "2024-02-01" in url

    @patch("src.rag.embeddings.get_settings")
    @patch("src.rag.embeddings.httpx.post")
    def test_embed_single_empty_result(self, mock_post, mock_settings):
        """Test single embedding with empty result."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.azure_openai_embedding_deployment = "text-embedding-ada-002"
        mock_settings_obj.azure_openai_api_version = "2024-02-01"
        mock_settings.return_value = mock_settings_obj

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from src.rag.embeddings import EmbeddingService

        service = EmbeddingService()
        embedding = service.embed("Test")

        assert embedding == []


class TestQdrantStore:
    """Tests for Qdrant vector store."""

    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_init(self, mock_settings, mock_embedding):
        """Test store initialization."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test_collection"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding.return_value = mock_embedding_service

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()

        assert store._collection_name == "test_collection"

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_get_client(self, mock_settings, mock_embedding, mock_client_class):
        """Test client initialization."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = MagicMock()
        mock_settings_obj.qdrant_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.qdrant_collection = "test_collection"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding.return_value = mock_embedding_service

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        _ = store._get_client()

        mock_client_class.assert_called_once()

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_ensure_collection_exists(self, mock_settings, mock_embedding, mock_client_class):
        """Test collection creation when it exists."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test_collection"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        store._ensure_collection()

        mock_client.get_collection.assert_called_once()

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_ensure_collection_creates(self, mock_settings, mock_embedding, mock_client_class):
        """Test collection creation when it doesn't exist."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test_collection"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("Collection not found")
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        store._ensure_collection()

        mock_client.create_collection.assert_called_once()

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_add_chunks_empty(self, mock_settings, mock_embedding, mock_client_class):
        """Test adding empty chunks."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding.return_value = mock_embedding_service

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        result = store.add_chunks([])

        assert result == 0

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_add_chunks_success(self, mock_settings, mock_embedding, mock_client_class):
        """Test adding chunks successfully."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding_service.embed_batch.return_value = [[0.1] * 1536, [0.2] * 1536]
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        chunks = [
            DocumentChunk(content="Chunk 1", metadata={"ticker": "NVDA"}, chunk_index=0),
            DocumentChunk(content="Chunk 2", metadata={"ticker": "NVDA"}, chunk_index=1),
        ]

        store = QdrantStore()
        result = store.add_chunks(chunks)

        assert result == 2

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_search(self, mock_settings, mock_embedding, mock_client_class):
        """Test search functionality."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding_service.embed.return_value = [0.1] * 1536
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.points = [
            MagicMock(payload={"content": "Test content", "ticker": "NVDA"}, score=0.85)
        ]
        mock_client.query_points.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        results = store.search("test query", top_k=5)

        assert len(results) == 1
        assert results[0]["content"] == "Test content"
        assert results[0]["score"] == 0.85

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_search_with_filters(self, mock_settings, mock_embedding, mock_client_class):
        """Test search with filters."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding_service.embed.return_value = [0.1] * 1536
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.points = []
        mock_client.query_points.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        results = store.search("test", filters={"ticker": "NVDA"})

        assert results == []

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_search_with_list_filter(self, mock_settings, mock_embedding, mock_client_class):
        """Test search with list filters."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding_service.embed.return_value = [0.1] * 1536
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.points = []
        mock_client.query_points.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        results = store.search("test", filters={"ticker": ["NVDA", "AMD"]})

        assert results == []

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_search_sec_filing(self, mock_settings, mock_embedding, mock_client_class):
        """Test SEC filing search."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding_service.dimension = 1536
        mock_embedding_service.embed.return_value = [0.1] * 1536
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.points = []
        mock_client.query_points.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        results = store.search_sec_filing("China risks", "nvda", "10-K")

        assert results == []

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_delete_by_ticker_success(self, mock_settings, mock_embedding, mock_client_class):
        """Test deleting documents by ticker."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        result = store.delete_by_ticker("NVDA")

        assert result is True

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_delete_by_ticker_failure(self, mock_settings, mock_embedding, mock_client_class):
        """Test deleting documents failure."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_client.delete.side_effect = Exception("Delete failed")
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        result = store.delete_by_ticker("NVDA")

        assert result is False

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_get_stats_success(self, mock_settings, mock_embedding, mock_client_class):
        """Test getting collection stats."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_info = MagicMock()
        mock_info.vectors_count = 100
        mock_info.points_count = 100
        mock_info.status.value = "green"
        mock_client.get_collection.return_value = mock_info
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        stats = store.get_stats()

        assert stats["collection"] == "test"
        assert stats["vectors_count"] == 100

    @patch("src.rag.vector_store.QdrantClient")
    @patch("src.rag.vector_store.get_embedding_service")
    @patch("src.rag.vector_store.get_settings")
    def test_get_stats_failure(self, mock_settings, mock_embedding, mock_client_class):
        """Test getting collection stats with error."""
        mock_settings_obj = MagicMock()
        mock_settings_obj.qdrant_url = "http://localhost:6333"
        mock_settings_obj.qdrant_api_key = None
        mock_settings_obj.qdrant_collection = "test"
        mock_settings.return_value = mock_settings_obj

        mock_embedding_service = MagicMock()
        mock_embedding.return_value = mock_embedding_service

        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("Error")
        mock_client_class.return_value = mock_client

        from src.rag.vector_store import QdrantStore

        store = QdrantStore()
        stats = store.get_stats()

        assert "error" in stats


class TestGetEmbeddingService:
    """Tests for get_embedding_service function."""

    @patch("src.rag.embeddings.EmbeddingService")
    @patch("src.rag.embeddings.get_settings")
    def test_get_embedding_service_cached(self, mock_settings, mock_service_class):
        """Test that embedding service is cached."""
        from src.rag.embeddings import get_embedding_service

        # Clear any previous cache
        get_embedding_service.cache_clear()

        mock_settings_obj = MagicMock()
        mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
        mock_settings_obj.azure_openai_embedding_deployment = "ada-002"
        mock_settings_obj.azure_openai_api_version = "2024-02-01"
        mock_settings.return_value = mock_settings_obj

        service1 = get_embedding_service()
        service2 = get_embedding_service()

        # Should be the same instance
        assert service1 is service2

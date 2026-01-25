"""Document chunking for RAG pipeline."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class DocumentChunk:
    """A chunk of text from a document."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }


class DocumentChunker:
    """Intelligent document chunking for SEC filings.

    Handles large documents (200+ pages) with:
    - Semantic chunking respecting paragraph boundaries
    - Overlap for context preservation
    - Metadata extraction (sections, page numbers)
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ) -> None:
        """Initialize chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            min_chunk_size: Minimum chunk size (smaller chunks are merged)
        """
        self._chunk_size = chunk_size
        self._overlap = chunk_overlap
        self._min_size = min_chunk_size

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove page numbers and headers
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)
        # Normalize line breaks
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r"\n\n+", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _find_section_header(self, text: str) -> str | None:
        """Extract section header from text if present."""
        # Common SEC filing section patterns
        patterns = [
            r"^(ITEM\s+\d+[A-Z]?\.?\s*[-–—]?\s*.+?)(?:\n|$)",
            r"^(PART\s+[IVX]+\.?\s*[-–—]?\s*.+?)(?:\n|$)",
            r"^(RISK\s+FACTORS)(?:\n|$)",
            r"^(MANAGEMENT\'S\s+DISCUSSION)(?:\n|$)",
            r"^(FINANCIAL\s+STATEMENTS)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return None

    def chunk_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to all chunks

        Returns:
            List of DocumentChunk objects
        """
        text = self._clean_text(text)
        base_metadata = metadata or {}

        if len(text) <= self._chunk_size:
            return [
                DocumentChunk(
                    content=text,
                    metadata=base_metadata,
                    chunk_index=0,
                    start_char=0,
                    end_char=len(text),
                )
            ]

        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = []
        current_length = 0
        current_start = 0
        char_position = 0
        current_section = None

        for para in paragraphs:
            para_length = len(para)

            # Check for section header
            section = self._find_section_header(para)
            if section:
                current_section = section

            # If adding this paragraph exceeds chunk size
            if current_length + para_length > self._chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunk_metadata = {**base_metadata}
                if current_section:
                    chunk_metadata["section"] = current_section

                chunks.append(
                    DocumentChunk(
                        content=chunk_text,
                        metadata=chunk_metadata,
                        chunk_index=len(chunks),
                        start_char=current_start,
                        end_char=char_position,
                    )
                )

                # Start new chunk with overlap
                overlap_paras = []
                overlap_length = 0
                for p in reversed(current_chunk):
                    if overlap_length + len(p) <= self._overlap:
                        overlap_paras.insert(0, p)
                        overlap_length += len(p)
                    else:
                        break

                current_chunk = overlap_paras
                current_length = overlap_length
                current_start = char_position - overlap_length

            current_chunk.append(para)
            current_length += para_length
            char_position += para_length + 2  # +2 for \n\n

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            if len(chunk_text) >= self._min_size:
                chunk_metadata = {**base_metadata}
                if current_section:
                    chunk_metadata["section"] = current_section

                chunks.append(
                    DocumentChunk(
                        content=chunk_text,
                        metadata=chunk_metadata,
                        chunk_index=len(chunks),
                        start_char=current_start,
                        end_char=char_position,
                    )
                )

        logger.info("text_chunked", num_chunks=len(chunks), total_chars=len(text))
        return chunks

    def chunk_file(self, file_path: Path | str) -> list[DocumentChunk]:
        """Chunk a text file.

        Args:
            file_path: Path to text file

        Returns:
            List of DocumentChunk objects
        """
        path = Path(file_path)

        if not path.exists():
            logger.error("file_not_found", path=str(path))
            return []

        text = path.read_text(encoding="utf-8", errors="ignore")
        metadata = {
            "source": str(path),
            "filename": path.name,
        }

        return self.chunk_text(text, metadata)

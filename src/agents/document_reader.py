"""Document Reader Agent for SEC filing analysis with RAG.

Enhanced with hybrid search (BM25 + dense) and reranking.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from src.rag import DocumentChunker, QdrantStore
from src.rag.hybrid_search import HybridSearcher
from src.rag.reranker import KeywordReranker
from src.tools import SECEdgarTool

logger = structlog.get_logger()


@dataclass
class DocumentSearchResult:
    """Result from document search."""

    ticker: str
    filing_type: str
    filing_date: str | None
    query: str
    passages: list[dict[str, Any]]
    summary: str
    errors: list[str]


class DocumentReaderAgent:
    """Agent for downloading and searching SEC filings.

    Responsibilities:
    - Download 10-K reports from SEC EDGAR
    - Chunk documents for RAG
    - Index in vector store (with BM25 hybrid search)
    - Search for relevant passages
    - Rerank results for improved relevance
    """

    def __init__(self, use_hybrid: bool = True, use_reranker: bool = True) -> None:
        """Initialize document reader agent.

        Args:
            use_hybrid: Enable hybrid search (BM25 + dense vectors).
            use_reranker: Enable keyword reranking for improved relevance.
        """
        self._sec_tool = SECEdgarTool()
        self._chunker = DocumentChunker(
            chunk_size=1500,  # Larger chunks for financial docs
            chunk_overlap=300,
        )
        self._vector_store = QdrantStore()
        self._hybrid_searcher = HybridSearcher(alpha=0.6) if use_hybrid else None
        self._reranker = KeywordReranker() if use_reranker else None
        self._use_hybrid = use_hybrid
        self._use_reranker = use_reranker
        self._temp_dir = Path(tempfile.gettempdir()) / "equity_research_docs"
        self._temp_dir.mkdir(exist_ok=True)

        # Cache for hybrid search index
        self._indexed_documents: dict[str, list[str]] = {}
        self._indexed_metadata: dict[str, list[dict]] = {}

    def _extract_text_from_html(self, file_path: Path) -> str:
        """Extract text from SEC HTML filing."""
        try:
            # Try unstructured for better parsing
            from unstructured.partition.html import partition_html  # pragma: no cover

            elements = partition_html(str(file_path))  # pragma: no cover
            text = "\n\n".join([str(el) for el in elements])  # pragma: no cover
            return text  # pragma: no cover
        except ImportError:
            # Fallback to basic HTML parsing
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []

                def handle_data(self, data):
                    text = data.strip()
                    if text:
                        self.text_parts.append(text)

            content = file_path.read_text(encoding="utf-8", errors="ignore")
            parser = TextExtractor()
            parser.feed(content)
            return "\n".join(parser.text_parts)
        except Exception as e:
            logger.error("text_extraction_failed", path=str(file_path), error=str(e))
            # Last resort: just read the file
            return file_path.read_text(encoding="utf-8", errors="ignore")

    def index_filing(self, ticker: str, form_type: str = "10-K") -> bool:
        """Download and index a SEC filing.

        Args:
            ticker: Stock ticker symbol
            form_type: SEC form type

        Returns:
            True if successful
        """
        ticker = ticker.upper()

        # Get filing info
        if form_type == "10-K":
            filing = self._sec_tool.get_latest_10k(ticker)
        else:
            logger.warning("unsupported_form_type", form_type=form_type)
            return False

        if not filing:
            logger.error("filing_not_found", ticker=ticker, form_type=form_type)
            return False

        # Download the filing
        file_path = self._sec_tool.download_filing(filing, str(self._temp_dir))
        if not file_path:
            logger.error("filing_download_failed", ticker=ticker)
            return False

        # Extract text
        text = self._extract_text_from_html(file_path)
        if not text or len(text) < 1000:
            logger.error("text_extraction_failed", ticker=ticker, length=len(text) if text else 0)
            return False

        logger.info("text_extracted", ticker=ticker, chars=len(text))

        # Chunk the document
        metadata = {
            "ticker": ticker,
            "form_type": form_type,
            "filing_date": filing.filing_date,
            "company_name": filing.company_name,
            "accession_number": filing.accession_number,
            "source_url": filing.file_url,
        }

        chunks = self._chunker.chunk_text(text, metadata)

        if not chunks:
            logger.error("chunking_failed", ticker=ticker)
            return False

        # Delete old documents for this ticker before indexing new ones
        self._vector_store.delete_by_ticker(ticker)

        # Index chunks
        indexed = self._vector_store.add_chunks(chunks)
        logger.info("filing_indexed", ticker=ticker, chunks=indexed)

        return indexed > 0

    def search_filing(
        self,
        ticker: str,
        query: str,
        form_type: str = "10-K",
        top_k: int = 5,
        auto_index: bool = True,
    ) -> DocumentSearchResult:
        """Search within a SEC filing using hybrid search + reranking.

        Args:
            ticker: Stock ticker symbol
            query: Search query (e.g., "China risks", "supply chain")
            form_type: SEC form type
            top_k: Number of passages to return
            auto_index: Auto-download and index if not found

        Returns:
            DocumentSearchResult with relevant passages
        """
        ticker = ticker.upper()
        errors = []

        # Get more results initially for reranking
        fetch_k = top_k * 3 if self._use_reranker else top_k

        # Try to search first
        results = self._vector_store.search_sec_filing(
            query=query,
            ticker=ticker,
            form_type=form_type,
            top_k=fetch_k,
        )

        # If no results and auto_index is enabled, try indexing
        if not results and auto_index:
            logger.info("auto_indexing", ticker=ticker, form_type=form_type)
            indexed = self.index_filing(ticker, form_type)

            if indexed:
                results = self._vector_store.search_sec_filing(
                    query=query,
                    ticker=ticker,
                    form_type=form_type,
                    top_k=fetch_k,
                )
            else:
                errors.append(f"Failed to index {form_type} for {ticker}")

        # Apply reranking if enabled
        if results and self._use_reranker and self._reranker:
            logger.info("applying_reranker", ticker=ticker, query=query, initial_count=len(results))
            reranked = self._reranker.rerank(query, results, top_k=top_k)
            results = [
                {
                    "content": r.content,
                    "score": r.final_score,
                    "metadata": r.metadata,
                    "rerank_boost": r.rerank_score,
                }
                for r in reranked
            ]
            logger.info("reranking_complete", final_count=len(results))
        else:
            # Just trim to top_k
            results = results[:top_k]

        # Get filing date from results metadata
        filing_date = None
        if results:
            filing_date = results[0].get("metadata", {}).get("filing_date")

        # Generate summary
        summary = self._generate_summary(ticker, query, results)

        return DocumentSearchResult(
            ticker=ticker,
            filing_type=form_type,
            filing_date=filing_date,
            query=query,
            passages=results,
            summary=summary,
            errors=errors,
        )

    def _generate_summary(
        self,
        ticker: str,
        query: str,
        results: list[dict[str, Any]],
    ) -> str:
        """Generate a summary of search results."""
        if not results:
            return f"No relevant passages found for '{query}' in {ticker}'s SEC filings."

        lines = [f"## SEC Filing Analysis: {ticker}\n"]
        lines.append(f"**Search Query**: {query}\n")
        lines.append(f"**Found {len(results)} relevant passages**\n")

        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            section = metadata.get("section", "Unknown Section")

            # Truncate content for summary
            preview = content[:500] + "..." if len(content) > 500 else content

            lines.append(f"### Passage {i} (Relevance: {score:.2f})")
            lines.append(f"**Section**: {section}")
            lines.append("```")
            lines.append(preview)
            lines.append("```\n")

        return "\n".join(lines)


def run_document_reader_node(state: dict) -> dict:
    """LangGraph node function for document reader agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with document analysis
    """
    tickers = state.get("tickers", [])
    document_queries = state.get("document_queries", [])

    if not tickers or not document_queries:
        return {
            "document_analysis": None,
            "errors": state.get("errors", []) + ["No tickers or queries provided"],
        }

    agent = DocumentReaderAgent()
    all_results = []
    all_errors = []

    for ticker in tickers:
        for query in document_queries:
            result = agent.search_filing(ticker, query)
            all_results.append(
                {
                    "ticker": result.ticker,
                    "query": result.query,
                    "filing_date": result.filing_date,
                    "passages": result.passages,
                    "summary": result.summary,
                }
            )
            all_errors.extend(result.errors)

    return {
        "document_analysis": all_results,
        "errors": state.get("errors", []) + all_errors,
    }

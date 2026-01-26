"""Hybrid search combining dense embeddings with BM25 sparse retrieval."""

import math
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np


@dataclass
class SearchResult:
    """Search result with combined score."""

    content: str
    dense_score: float
    sparse_score: float
    combined_score: float
    metadata: dict


class BM25:
    """BM25 sparse retrieval implementation.
    
    Okapi BM25 ranking function for keyword-based search.
    Complements dense embeddings for better recall.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize BM25.
        
        Args:
            k1: Term frequency saturation parameter.
            b: Length normalization parameter.
        """
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Counter = Counter()
        self.idf: dict[str, float] = {}
        self.corpus_size: int = 0

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        text = text.lower()
        tokens = re.findall(r"\b[a-z0-9]+\b", text)
        return tokens

    def fit(self, documents: list[str]) -> None:
        """Fit BM25 on a corpus of documents.
        
        Args:
            documents: List of document texts.
        """
        self.corpus = [self._tokenize(doc) for doc in documents]
        self.corpus_size = len(self.corpus)
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avg_doc_length = sum(self.doc_lengths) / max(self.corpus_size, 1)

        # Calculate document frequencies
        self.doc_freqs = Counter()
        for doc in self.corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.doc_freqs[term] += 1

        # Calculate IDF for all terms
        self.idf = {}
        for term, df in self.doc_freqs.items():
            # IDF with smoothing
            self.idf[term] = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1)

    def _score_document(self, query_tokens: list[str], doc_idx: int) -> float:
        """Calculate BM25 score for a single document."""
        doc = self.corpus[doc_idx]
        doc_len = self.doc_lengths[doc_idx]
        term_freqs = Counter(doc)

        score = 0.0
        for term in query_tokens:
            if term not in self.idf:
                continue

            tf = term_freqs.get(term, 0)
            idf = self.idf[term]

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """Search for documents matching the query.
        
        Args:
            query: Search query.
            top_k: Number of results to return.
            
        Returns:
            List of (doc_index, score) tuples sorted by score descending.
        """
        query_tokens = self._tokenize(query)
        scores = []

        for idx in range(self.corpus_size):
            score = self._score_document(query_tokens, idx)
            if score > 0:
                scores.append((idx, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class HybridSearcher:
    """Combines dense embeddings with BM25 sparse search.
    
    Uses Reciprocal Rank Fusion (RRF) to merge results from both methods.
    """

    def __init__(self, alpha: float = 0.5, rrf_k: int = 60) -> None:
        """Initialize hybrid searcher.
        
        Args:
            alpha: Weight for dense search (1-alpha for sparse).
            rrf_k: RRF constant (default 60 is standard).
        """
        self.alpha = alpha
        self.rrf_k = rrf_k
        self.bm25 = BM25()
        self.documents: list[str] = []
        self.metadata: list[dict] = []

    def index(self, documents: list[str], metadata: list[dict] | None = None) -> None:
        """Index documents for hybrid search.
        
        Args:
            documents: List of document texts.
            metadata: Optional metadata for each document.
        """
        self.documents = documents
        self.metadata = metadata or [{} for _ in documents]
        self.bm25.fit(documents)

    def search(
        self,
        query: str,
        query_embedding: list[float],
        doc_embeddings: list[list[float]],
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Perform hybrid search combining dense and sparse results.
        
        Args:
            query: Search query text.
            query_embedding: Dense embedding of the query.
            doc_embeddings: Dense embeddings of all documents.
            top_k: Number of results to return.
            
        Returns:
            List of SearchResult objects with combined scores.
        """
        # Get BM25 sparse results
        sparse_results = self.bm25.search(query, top_k=top_k * 2)
        
        # Calculate dense similarities
        query_vec = np.array(query_embedding)
        dense_scores = []
        for idx, doc_emb in enumerate(doc_embeddings):
            doc_vec = np.array(doc_emb)
            # Cosine similarity
            similarity = np.dot(query_vec, doc_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-8
            )
            dense_scores.append((idx, float(similarity)))

        # Sort dense by score
        dense_scores.sort(key=lambda x: x[1], reverse=True)
        dense_results = dense_scores[: top_k * 2]

        # Reciprocal Rank Fusion
        rrf_scores: dict[int, float] = {}

        # Add dense scores with RRF
        for rank, (idx, score) in enumerate(dense_results):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + self.alpha / (self.rrf_k + rank + 1)

        # Add sparse scores with RRF
        for rank, (idx, score) in enumerate(sparse_results):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + (1 - self.alpha) / (self.rrf_k + rank + 1)

        # Sort by combined RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Build result objects
        results = []
        for idx, combined_score in sorted_results[:top_k]:
            # Find individual scores
            dense_score = next((s for i, s in dense_scores if i == idx), 0.0)
            sparse_score = next((s for i, s in sparse_results if i == idx), 0.0)

            results.append(
                SearchResult(
                    content=self.documents[idx],
                    dense_score=dense_score,
                    sparse_score=sparse_score,
                    combined_score=combined_score,
                    metadata=self.metadata[idx],
                )
            )

        return results


def create_hybrid_searcher(alpha: float = 0.5) -> HybridSearcher:
    """Create a hybrid searcher with default settings.
    
    Args:
        alpha: Weight for dense search (0.5 = equal weight).
        
    Returns:
        Configured HybridSearcher instance.
    """
    return HybridSearcher(alpha=alpha)

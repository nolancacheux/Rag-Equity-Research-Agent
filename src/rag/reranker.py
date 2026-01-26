"""Reranking module for improving search result relevance.

Implements multiple reranking strategies:
1. Cross-encoder scoring (if sentence-transformers available)
2. LLM-based reranking (uses existing LLM)
3. Keyword-boost reranking (zero dependencies)
"""

import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class RankedResult:
    """Search result with reranking score."""

    content: str
    original_score: float
    rerank_score: float
    final_score: float
    metadata: dict


class KeywordReranker:
    """Simple keyword-based reranker (zero external dependencies).
    
    Boosts results that contain query terms and financial keywords.
    """

    # Financial domain keywords that indicate relevance
    BOOST_KEYWORDS = {
        "revenue": 1.2,
        "earnings": 1.2,
        "profit": 1.1,
        "margin": 1.1,
        "growth": 1.1,
        "guidance": 1.3,
        "outlook": 1.2,
        "risk": 1.2,
        "china": 1.3,
        "supply chain": 1.2,
        "competition": 1.1,
        "market share": 1.1,
        "operating income": 1.2,
        "cash flow": 1.1,
        "debt": 1.1,
        "acquisition": 1.1,
    }

    def rerank(
        self, query: str, results: list[dict], top_k: int = 10
    ) -> list[RankedResult]:
        """Rerank results based on keyword matching.
        
        Args:
            query: Original search query.
            results: List of search results with 'content' and 'score' keys.
            top_k: Number of results to return.
            
        Returns:
            Reranked results.
        """
        query_lower = query.lower()
        query_terms = set(re.findall(r"\b\w+\b", query_lower))

        ranked = []
        for result in results:
            content = result.get("content", "")
            content_lower = content.lower()
            original_score = result.get("score", 0.5)

            # Calculate rerank score
            rerank_score = 1.0

            # Boost for query term matches
            for term in query_terms:
                if len(term) > 2 and term in content_lower:
                    rerank_score *= 1.1

            # Boost for financial keywords
            for keyword, boost in self.BOOST_KEYWORDS.items():
                if keyword in content_lower:
                    rerank_score *= boost

            # Penalize very short content
            if len(content) < 100:
                rerank_score *= 0.7

            # Combine scores
            final_score = original_score * rerank_score

            ranked.append(
                RankedResult(
                    content=content,
                    original_score=original_score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                    metadata=result.get("metadata", {}),
                )
            )

        # Sort by final score
        ranked.sort(key=lambda x: x.final_score, reverse=True)
        return ranked[:top_k]


class LLMReranker:
    """LLM-based reranker using existing LLM configuration.
    
    Asks the LLM to score relevance of each result.
    More accurate but slower and uses LLM tokens.
    """

    def __init__(self, llm=None) -> None:
        """Initialize LLM reranker.
        
        Args:
            llm: LangChain LLM instance. If None, will create from settings.
        """
        self._llm = llm

    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            from src.agents.synthesizer import SynthesizerAgent
            agent = SynthesizerAgent()
            self._llm = agent._llm
        return self._llm

    async def rerank(
        self, query: str, results: list[dict], top_k: int = 5
    ) -> list[RankedResult]:
        """Rerank results using LLM scoring.
        
        Args:
            query: Original search query.
            results: List of search results.
            top_k: Number of results to return.
            
        Returns:
            Reranked results.
        """
        llm = self._get_llm()
        ranked = []

        # Process in batch for efficiency
        # Limit to top candidates to save tokens
        candidates = results[:min(len(results), top_k * 2)]

        for result in candidates:
            content = result.get("content", "")[:500]  # Truncate for token efficiency
            original_score = result.get("score", 0.5)

            # Ask LLM to score relevance
            prompt = f"""Rate the relevance of this text to the query on a scale of 0-10.
            
Query: {query}

Text: {content}

Respond with ONLY a number from 0-10."""

            try:
                response = await llm.ainvoke(prompt)
                score_text = response.content.strip()
                # Extract number
                match = re.search(r"\b(\d+(?:\.\d+)?)\b", score_text)
                llm_score = float(match.group(1)) / 10 if match else 0.5
            except Exception as e:
                logger.debug("llm_rerank_failed", error=str(e))
                llm_score = 0.5

            final_score = (original_score + llm_score) / 2

            ranked.append(
                RankedResult(
                    content=result.get("content", ""),
                    original_score=original_score,
                    rerank_score=llm_score,
                    final_score=final_score,
                    metadata=result.get("metadata", {}),
                )
            )

        ranked.sort(key=lambda x: x.final_score, reverse=True)
        return ranked[:top_k]


class HybridReranker:
    """Combines multiple reranking strategies.
    
    1. First pass: Keyword reranking (fast)
    2. Second pass: LLM reranking on top candidates (accurate)
    """

    def __init__(self, use_llm: bool = False) -> None:
        """Initialize hybrid reranker.
        
        Args:
            use_llm: Whether to use LLM for second pass.
        """
        self.keyword_reranker = KeywordReranker()
        self.llm_reranker = LLMReranker() if use_llm else None
        self.use_llm = use_llm

    async def rerank(
        self, query: str, results: list[dict], top_k: int = 10
    ) -> list[RankedResult]:
        """Rerank using hybrid strategy.
        
        Args:
            query: Original search query.
            results: List of search results.
            top_k: Number of results to return.
            
        Returns:
            Reranked results.
        """
        # First pass: keyword reranking
        keyword_ranked = self.keyword_reranker.rerank(query, results, top_k=top_k * 2)

        if not self.use_llm or self.llm_reranker is None:
            return keyword_ranked[:top_k]

        # Second pass: LLM reranking on top candidates
        top_candidates = [
            {
                "content": r.content,
                "score": r.final_score,
                "metadata": r.metadata,
            }
            for r in keyword_ranked[:top_k]
        ]

        return await self.llm_reranker.rerank(query, top_candidates, top_k=top_k)


def create_reranker(use_llm: bool = False) -> HybridReranker:
    """Create a reranker instance.
    
    Args:
        use_llm: Whether to use LLM for improved accuracy (costs tokens).
        
    Returns:
        Configured reranker.
    """
    return HybridReranker(use_llm=use_llm)

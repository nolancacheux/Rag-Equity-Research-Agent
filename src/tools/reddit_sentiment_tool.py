"""Reddit sentiment analysis for stocks using free API."""

import re
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class RedditPost:
    """Reddit post data."""

    title: str
    content: str
    subreddit: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    sentiment: str  # bullish, bearish, neutral


@dataclass
class RedditSentiment:
    """Aggregated Reddit sentiment for a ticker."""

    ticker: str
    total_posts: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    sentiment_score: float  # -1 to 1
    top_posts: list[RedditPost]
    trending_keywords: list[str]


class RedditSentimentTool:
    """Analyze Reddit sentiment for stocks.
    
    Uses Reddit's public JSON API (no auth needed for read-only).
    Focuses on r/wallstreetbets, r/stocks, r/investing.
    """

    SUBREDDITS = ["wallstreetbets", "stocks", "investing", "options", "stockmarket"]
    
    # Sentiment keywords
    BULLISH_WORDS = {
        "buy", "long", "calls", "moon", "rocket", "bullish", "undervalued",
        "growth", "beat", "upgrade", "breakout", "squeeze", "tendies",
        "diamond hands", "to the moon", "yolo", "all in", "loading up",
    }
    
    BEARISH_WORDS = {
        "sell", "short", "puts", "crash", "bearish", "overvalued",
        "decline", "miss", "downgrade", "breakdown", "dump", "tanking",
        "paper hands", "bag holder", "red", "loss", "bleeding",
    }

    def __init__(self) -> None:
        """Initialize Reddit sentiment tool."""
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={
                "User-Agent": "EquityResearchAgent/1.0 (Financial Research Bot)"
            },
        )

    async def analyze_sentiment(
        self, ticker: str, limit: int = 50
    ) -> RedditSentiment:
        """Analyze Reddit sentiment for a ticker.
        
        Args:
            ticker: Stock ticker symbol.
            limit: Max posts to analyze per subreddit.
            
        Returns:
            RedditSentiment with aggregated analysis.
        """
        ticker = ticker.upper()
        all_posts: list[RedditPost] = []

        # Search each subreddit
        for subreddit in self.SUBREDDITS:
            posts = await self._search_subreddit(subreddit, ticker, limit=limit // len(self.SUBREDDITS))
            all_posts.extend(posts)

        # Analyze sentiment
        bullish = sum(1 for p in all_posts if p.sentiment == "bullish")
        bearish = sum(1 for p in all_posts if p.sentiment == "bearish")
        neutral = sum(1 for p in all_posts if p.sentiment == "neutral")
        total = len(all_posts)

        # Calculate sentiment score (-1 to 1)
        if total > 0:
            sentiment_score = (bullish - bearish) / total
        else:
            sentiment_score = 0.0

        # Extract trending keywords
        keywords = self._extract_keywords(all_posts, ticker)

        # Sort by score for top posts
        top_posts = sorted(all_posts, key=lambda p: p.score, reverse=True)[:10]

        return RedditSentiment(
            ticker=ticker,
            total_posts=total,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            sentiment_score=round(sentiment_score, 3),
            top_posts=top_posts,
            trending_keywords=keywords,
        )

    async def _search_subreddit(
        self, subreddit: str, ticker: str, limit: int = 10
    ) -> list[RedditPost]:
        """Search a subreddit for ticker mentions."""
        try:
            # Reddit public JSON API
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                "q": f"${ticker} OR {ticker}",
                "restrict_sr": "on",
                "sort": "relevance",
                "t": "week",  # Last week
                "limit": limit,
            }

            response = await self.client.get(url, params=params)
            
            if response.status_code != 200:
                logger.debug("reddit_search_failed", subreddit=subreddit, status=response.status_code)
                return []

            data = response.json()
            posts = []

            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                
                title = post_data.get("title", "")
                content = post_data.get("selftext", "")
                full_text = f"{title} {content}".lower()

                # Determine sentiment
                sentiment = self._analyze_text_sentiment(full_text)

                posts.append(
                    RedditPost(
                        title=title,
                        content=content[:500],  # Truncate
                        subreddit=subreddit,
                        score=post_data.get("score", 0),
                        num_comments=post_data.get("num_comments", 0),
                        created_utc=post_data.get("created_utc", 0),
                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                        sentiment=sentiment,
                    )
                )

            return posts

        except Exception as e:
            logger.debug("reddit_search_error", subreddit=subreddit, error=str(e))
            return []

    def _analyze_text_sentiment(self, text: str) -> str:
        """Analyze sentiment of text using keyword matching."""
        text_lower = text.lower()
        
        bullish_score = sum(1 for word in self.BULLISH_WORDS if word in text_lower)
        bearish_score = sum(1 for word in self.BEARISH_WORDS if word in text_lower)

        if bullish_score > bearish_score:
            return "bullish"
        elif bearish_score > bullish_score:
            return "bearish"
        else:
            return "neutral"

    def _extract_keywords(self, posts: list[RedditPost], ticker: str) -> list[str]:
        """Extract trending keywords from posts."""
        from collections import Counter

        # Common words to exclude
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "and", "or", "but",
            "if", "then", "else", "when", "where", "why", "how", "what",
            "this", "that", "these", "those", "i", "you", "he", "she",
            "it", "we", "they", "my", "your", "his", "her", "its", "our",
            "their", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            ticker.lower(), "stock", "share", "price", "market",
        }

        word_counts: Counter = Counter()
        
        for post in posts:
            text = f"{post.title} {post.content}".lower()
            words = re.findall(r"\b[a-z]{3,}\b", text)
            for word in words:
                if word not in stop_words:
                    word_counts[word] += 1

        # Return top keywords
        return [word for word, _ in word_counts.most_common(15)]

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


async def get_reddit_sentiment(ticker: str) -> RedditSentiment:
    """Convenience function to get Reddit sentiment.
    
    Args:
        ticker: Stock ticker symbol.
        
    Returns:
        RedditSentiment analysis.
    """
    tool = RedditSentimentTool()
    try:
        return await tool.analyze_sentiment(ticker)
    finally:
        await tool.close()

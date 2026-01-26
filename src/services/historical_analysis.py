"""Historical analysis service for price reactions and patterns."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger()


@dataclass
class EarningsReaction:
    """Stock reaction to an earnings report."""

    date: str
    quarter: str
    price_before: float
    price_after: float
    change_percent: float
    gap_percent: float  # Opening gap
    volume_ratio: float  # vs average


@dataclass
class HistoricalPattern:
    """Historical pattern analysis."""

    ticker: str
    avg_earnings_move: float
    positive_surprises: int
    negative_surprises: int
    beat_rate: float  # % of times beat expectations
    avg_gap: float
    largest_move: EarningsReaction | None
    recent_reactions: list[EarningsReaction]
    summary: str


@dataclass
class PriceHistory:
    """Price history data."""

    ticker: str
    period: str
    start_price: float
    end_price: float
    high: float
    low: float
    total_return: float
    volatility: float
    avg_volume: float
    summary: str


class HistoricalAnalysisService:
    """Analyze historical price data and patterns.
    
    Uses Yahoo Finance for all historical data (free).
    """

    def __init__(self) -> None:
        """Initialize historical analysis service."""
        pass

    def get_earnings_reactions(self, ticker: str, num_quarters: int = 8) -> HistoricalPattern:
        """Analyze historical earnings reactions.
        
        Args:
            ticker: Stock ticker symbol.
            num_quarters: Number of quarters to analyze.
            
        Returns:
            HistoricalPattern with reaction data.
        """
        import yfinance as yf
        import pandas as pd
        
        ticker = ticker.upper()
        
        try:
            stock = yf.Ticker(ticker)
            
            # Get historical earnings
            earnings_hist = stock.earnings_history
            if earnings_hist is None or earnings_hist.empty:
                return self._empty_pattern(ticker, "No earnings history available")
            
            # Get price history (2 years)
            hist = stock.history(period="2y")
            if hist.empty:
                return self._empty_pattern(ticker, "No price history available")
            
            reactions = []
            positive = 0
            negative = 0
            
            # Analyze each earnings date
            for _, row in earnings_hist.head(num_quarters).iterrows():
                try:
                    earnings_date = row.name
                    if hasattr(earnings_date, 'date'):
                        ed = earnings_date.date()
                    else:
                        ed = pd.to_datetime(earnings_date).date()
                    
                    # Find prices around earnings
                    # Day before
                    before_date = ed - timedelta(days=1)
                    # Day after (or next trading day)
                    after_date = ed + timedelta(days=1)
                    
                    # Get closest prices
                    before_mask = hist.index.date <= ed
                    after_mask = hist.index.date >= ed
                    
                    if not before_mask.any() or not after_mask.any():
                        continue
                    
                    price_before = hist[before_mask]["Close"].iloc[-1]
                    price_after = hist[after_mask]["Close"].iloc[0]
                    
                    # Calculate change
                    change = ((price_after - price_before) / price_before) * 100
                    
                    # Check if beat/miss
                    eps_actual = row.get("epsActual", 0)
                    eps_estimate = row.get("epsEstimate", 0)
                    
                    if eps_actual and eps_estimate:
                        if eps_actual > eps_estimate:
                            positive += 1
                        else:
                            negative += 1
                    
                    # Quarter string
                    quarter = f"Q{(ed.month - 1) // 3 + 1} {ed.year}"
                    
                    reactions.append(EarningsReaction(
                        date=str(ed),
                        quarter=quarter,
                        price_before=round(price_before, 2),
                        price_after=round(price_after, 2),
                        change_percent=round(change, 2),
                        gap_percent=round(change, 2),  # Simplified
                        volume_ratio=1.0,
                    ))
                    
                except Exception as e:
                    logger.debug("earnings_reaction_parse_error", error=str(e))
                    continue
            
            if not reactions:
                return self._empty_pattern(ticker, "Could not analyze earnings reactions")
            
            # Calculate stats
            moves = [abs(r.change_percent) for r in reactions]
            avg_move = sum(moves) / len(moves) if moves else 0
            
            total = positive + negative
            beat_rate = positive / total if total > 0 else 0.5
            
            avg_change = sum(r.change_percent for r in reactions) / len(reactions)
            
            largest = max(reactions, key=lambda x: abs(x.change_percent))
            
            summary = self._generate_pattern_summary(
                ticker, avg_move, positive, negative, beat_rate, avg_change, reactions
            )
            
            return HistoricalPattern(
                ticker=ticker,
                avg_earnings_move=round(avg_move, 2),
                positive_surprises=positive,
                negative_surprises=negative,
                beat_rate=round(beat_rate, 2),
                avg_gap=round(avg_change, 2),
                largest_move=largest,
                recent_reactions=reactions[:4],
                summary=summary,
            )
            
        except Exception as e:
            logger.error("earnings_reactions_failed", ticker=ticker, error=str(e))
            return self._empty_pattern(ticker, str(e))

    def get_price_history(self, ticker: str, period: str = "1y") -> PriceHistory:
        """Get price history and statistics.
        
        Args:
            ticker: Stock ticker symbol.
            period: Period (1mo, 3mo, 6mo, 1y, 2y, 5y).
            
        Returns:
            PriceHistory with statistics.
        """
        import yfinance as yf
        import numpy as np
        
        ticker = ticker.upper()
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return PriceHistory(
                    ticker=ticker,
                    period=period,
                    start_price=0,
                    end_price=0,
                    high=0,
                    low=0,
                    total_return=0,
                    volatility=0,
                    avg_volume=0,
                    summary=f"No price history for {ticker}",
                )
            
            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
            high = hist["High"].max()
            low = hist["Low"].min()
            total_return = ((end_price - start_price) / start_price) * 100
            
            # Calculate volatility (annualized)
            returns = hist["Close"].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 0 else 0
            
            avg_volume = hist["Volume"].mean()
            
            summary = self._generate_history_summary(
                ticker, period, start_price, end_price, high, low,
                total_return, volatility, avg_volume
            )
            
            return PriceHistory(
                ticker=ticker,
                period=period,
                start_price=round(start_price, 2),
                end_price=round(end_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                total_return=round(total_return, 2),
                volatility=round(volatility, 2),
                avg_volume=round(avg_volume),
                summary=summary,
            )
            
        except Exception as e:
            logger.error("price_history_failed", ticker=ticker, error=str(e))
            return PriceHistory(
                ticker=ticker,
                period=period,
                start_price=0,
                end_price=0,
                high=0,
                low=0,
                total_return=0,
                volatility=0,
                avg_volume=0,
                summary=f"Error getting history for {ticker}: {e}",
            )

    def _generate_pattern_summary(
        self,
        ticker: str,
        avg_move: float,
        positive: int,
        negative: int,
        beat_rate: float,
        avg_change: float,
        reactions: list[EarningsReaction],
    ) -> str:
        """Generate earnings pattern summary."""
        lines = [f"## Earnings Reaction Pattern: {ticker}"]
        lines.append("")
        lines.append(f"**Average Move**: ±{avg_move:.1f}%")
        lines.append(f"**Beat Rate**: {beat_rate:.0%} ({positive} beats, {negative} misses)")
        lines.append(f"**Avg Direction**: {avg_change:+.1f}%")
        lines.append("")
        
        lines.append("### Recent Reactions")
        for r in reactions[:4]:
            emoji = "🟢" if r.change_percent > 0 else "🔴"
            lines.append(f"- {r.quarter}: {r.change_percent:+.1f}% {emoji}")
        
        lines.append("")
        lines.append("*Past performance does not guarantee future results.*")
        
        return "\n".join(lines)

    def _generate_history_summary(
        self,
        ticker: str,
        period: str,
        start: float,
        end: float,
        high: float,
        low: float,
        total_return: float,
        volatility: float,
        avg_volume: float,
    ) -> str:
        """Generate price history summary."""
        emoji = "🟢" if total_return > 0 else "🔴"
        
        lines = [f"## Price History: {ticker} ({period})"]
        lines.append("")
        lines.append(f"**Return**: {total_return:+.1f}% {emoji}")
        lines.append(f"**Start**: ${start:.2f} → **End**: ${end:.2f}")
        lines.append(f"**52W Range**: ${low:.2f} - ${high:.2f}")
        lines.append(f"**Volatility**: {volatility:.1f}% (annualized)")
        lines.append(f"**Avg Volume**: {avg_volume/1e6:.1f}M")
        
        return "\n".join(lines)

    def _empty_pattern(self, ticker: str, reason: str) -> HistoricalPattern:
        """Return empty pattern."""
        return HistoricalPattern(
            ticker=ticker,
            avg_earnings_move=0,
            positive_surprises=0,
            negative_surprises=0,
            beat_rate=0.5,
            avg_gap=0,
            largest_move=None,
            recent_reactions=[],
            summary=f"Could not analyze {ticker}: {reason}",
        )

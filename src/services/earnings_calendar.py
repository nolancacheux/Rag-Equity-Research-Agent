"""Earnings calendar service using free Yahoo Finance data."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger()


@dataclass
class EarningsEvent:
    """Earnings event data."""

    ticker: str
    company_name: str | None
    earnings_date: str
    days_until: int
    eps_estimate: float | None
    revenue_estimate: float | None
    time_of_day: str | None  # BMO (before market), AMC (after market close)


@dataclass
class EarningsCalendar:
    """Earnings calendar result."""

    watchlist_events: list[EarningsEvent]
    upcoming_major: list[EarningsEvent]  # Big tech, etc.
    this_week: list[EarningsEvent]
    summary: str


class EarningsCalendarService:
    """Track earnings dates for watchlist and major stocks.
    
    Uses Yahoo Finance (free) for earnings dates.
    """

    # Major stocks to always track
    MAJOR_TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
        "JPM", "BAC", "WMT", "JNJ", "V", "MA", "HD", "PG",
    ]

    def __init__(self) -> None:
        """Initialize earnings calendar service."""
        pass

    def get_earnings_date(self, ticker: str) -> EarningsEvent | None:
        """Get next earnings date for a ticker.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            EarningsEvent or None if not found.
        """
        import yfinance as yf
        
        ticker = ticker.upper()
        
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            
            if calendar is None or calendar.empty:
                return None
            
            # Get earnings date
            earnings_date = None
            if "Earnings Date" in calendar.index:
                dates = calendar.loc["Earnings Date"]
                if len(dates) > 0:
                    earnings_date = dates.iloc[0]
            
            if earnings_date is None:
                return None
            
            # Calculate days until
            if hasattr(earnings_date, 'date'):
                earnings_dt = earnings_date.date()
            else:
                earnings_dt = datetime.strptime(str(earnings_date)[:10], "%Y-%m-%d").date()
            
            today = datetime.now().date()
            days_until = (earnings_dt - today).days
            
            # Get estimates
            eps_estimate = None
            revenue_estimate = None
            
            if "Earnings Average" in calendar.index:
                eps_estimate = calendar.loc["Earnings Average"].iloc[0]
            if "Revenue Average" in calendar.index:
                revenue_estimate = calendar.loc["Revenue Average"].iloc[0]
            
            # Get company name
            info = stock.info
            company_name = info.get("shortName") or info.get("longName")
            
            return EarningsEvent(
                ticker=ticker,
                company_name=company_name,
                earnings_date=str(earnings_dt),
                days_until=days_until,
                eps_estimate=eps_estimate,
                revenue_estimate=revenue_estimate,
                time_of_day=None,
            )
            
        except Exception as e:
            logger.debug("earnings_date_fetch_failed", ticker=ticker, error=str(e))
            return None

    def get_calendar(self, watchlist: list[str] | None = None) -> EarningsCalendar:
        """Get earnings calendar for watchlist and major stocks.
        
        Args:
            watchlist: Optional list of tickers to track.
            
        Returns:
            EarningsCalendar with upcoming events.
        """
        watchlist_events = []
        major_events = []
        this_week = []
        
        # Process watchlist
        if watchlist:
            for ticker in watchlist[:20]:  # Limit to 20
                event = self.get_earnings_date(ticker)
                if event and event.days_until >= 0:
                    watchlist_events.append(event)
        
        # Process major tickers (not in watchlist)
        watchlist_set = set(watchlist or [])
        for ticker in self.MAJOR_TICKERS:
            if ticker not in watchlist_set:
                event = self.get_earnings_date(ticker)
                if event and 0 <= event.days_until <= 30:
                    major_events.append(event)
        
        # Combine and find this week's events
        all_events = watchlist_events + major_events
        this_week = [e for e in all_events if 0 <= e.days_until <= 7]
        
        # Sort by date
        watchlist_events.sort(key=lambda x: x.days_until)
        major_events.sort(key=lambda x: x.days_until)
        this_week.sort(key=lambda x: x.days_until)
        
        summary = self._generate_summary(watchlist_events, major_events, this_week)
        
        return EarningsCalendar(
            watchlist_events=watchlist_events[:10],
            upcoming_major=major_events[:10],
            this_week=this_week[:10],
            summary=summary,
        )

    def _generate_summary(
        self,
        watchlist_events: list[EarningsEvent],
        major_events: list[EarningsEvent],
        this_week: list[EarningsEvent],
    ) -> str:
        """Generate calendar summary."""
        lines = ["## Earnings Calendar"]
        
        if this_week:
            lines.append("")
            lines.append("### This Week")
            for e in this_week[:5]:
                days_str = "TODAY" if e.days_until == 0 else f"in {e.days_until}d"
                lines.append(f"- **{e.ticker}** ({e.company_name or 'N/A'}): {e.earnings_date} ({days_str})")
        
        if watchlist_events:
            lines.append("")
            lines.append("### Your Watchlist")
            for e in watchlist_events[:5]:
                eps_str = f"EPS est: ${e.eps_estimate:.2f}" if e.eps_estimate else ""
                lines.append(f"- **{e.ticker}**: {e.earnings_date} ({e.days_until}d) {eps_str}")
        
        if major_events:
            lines.append("")
            lines.append("### Major Companies")
            for e in major_events[:5]:
                lines.append(f"- **{e.ticker}**: {e.earnings_date} ({e.days_until}d)")
        
        if not (this_week or watchlist_events or major_events):
            lines.append("")
            lines.append("No upcoming earnings found in the next 30 days.")
        
        return "\n".join(lines)

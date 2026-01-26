"""FastAPI application for Equity Research Agent."""

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.agents import run_research
from src.api.metrics import (
    ANALYSIS_DURATION,
    ANALYSIS_REQUESTS,
    ERRORS_TOTAL,
    QUOTE_REQUESTS,
    REQUEST_LATENCY,
    REQUESTS_TOTAL,
    metrics_endpoint,
)
from src.api.middleware.auth import verify_api_key
from src.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("starting_application", env=settings.app_env)
    yield
    logger.info("shutting_down_application")


app = FastAPI(
    title="Equity Research Agent",
    description="AI-powered real-time equity research with LangGraph",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - In production, configure ALLOWED_ORIGINS env var
# Default: restrictive in prod, permissive in dev
ALLOWED_ORIGINS = (
    ["*"] if not settings.is_production else []  # No CORS in prod (API-only, or configure via env)
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Safer default
    allow_methods=["GET", "POST"],  # Only what we need
    allow_headers=["Content-Type", "Authorization"],
)


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request model for analysis endpoint."""

    query: str = Field(
        ...,
        description="Research query (e.g., 'Analyze NVDA vs AMD P/E ratios')",
        min_length=10,
        max_length=1000,
    )
    tickers: list[str] | None = Field(
        None,
        description="Optional list of tickers (auto-detected if not provided)",
        max_length=5,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Analyze NVIDIA's current situation. Compare their P/E Ratio with AMD, and check their latest 10-K report for China-related risks.",
                    "tickers": ["NVDA", "AMD"],
                }
            ]
        }
    }


class AnalyzeResponse(BaseModel):
    """Response model for analysis endpoint."""

    success: bool
    report: dict[str, Any] | None = None
    market_data: dict[str, Any] | None = None
    errors: list[str] = []


class QuoteRequest(BaseModel):
    """Request model for quote endpoint."""

    ticker: str = Field(..., description="Stock ticker symbol", pattern=r"^[A-Z]{1,5}$")


class QuoteResponse(BaseModel):
    """Response model for quote endpoint."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    REQUESTS_TOTAL.labels(method="GET", endpoint="/health", status="200").inc()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@app.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint."""
    return await metrics_endpoint(request)


@app.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def analyze(request: Request, analysis_request: AnalyzeRequest) -> AnalyzeResponse:
    """Run equity research analysis.

    This endpoint:
    1. Fetches real-time market data from Yahoo Finance
    2. Downloads and analyzes SEC 10-K filings (if relevant)
    3. Searches recent news
    4. Synthesizes everything into a research report
    """
    import time

    start_time = time.time()
    try:
        logger.info("analysis_requested", query=analysis_request.query[:100])

        result = await run_research(
            query=analysis_request.query,
            tickers=analysis_request.tickers,
        )

        # Record metrics
        duration = time.time() - start_time
        ANALYSIS_DURATION.observe(duration)
        ANALYSIS_REQUESTS.labels(status="success").inc()
        REQUESTS_TOTAL.labels(method="POST", endpoint="/analyze", status="200").inc()
        REQUEST_LATENCY.labels(method="POST", endpoint="/analyze").observe(duration)

        return AnalyzeResponse(
            success=True,
            report=result.get("report"),
            market_data=result.get("market_data"),
            errors=result.get("errors", []),
        )

    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        ANALYSIS_REQUESTS.labels(status="error").inc()
        ERRORS_TOTAL.labels(type="analysis", endpoint="/analyze").inc()
        REQUESTS_TOTAL.labels(method="POST", endpoint="/analyze", status="500").inc()
        # Don't leak internal errors in production
        detail = str(e) if not settings.is_production else "Analysis failed"
        raise HTTPException(status_code=500, detail=detail) from None


@app.get("/quote/{ticker}", response_model=QuoteResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_quote(request: Request, ticker: str) -> QuoteResponse:
    """Get real-time stock quote.

    Returns current price, P/E ratio, market cap, and other metrics.
    """
    import time

    from src.tools import YFinanceTool

    start_time = time.time()
    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        REQUESTS_TOTAL.labels(method="GET", endpoint="/quote", status="400").inc()
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        tool = YFinanceTool()
        quote = tool.get_quote(ticker)

        duration = time.time() - start_time
        REQUEST_LATENCY.labels(method="GET", endpoint="/quote").observe(duration)

        if not quote:
            QUOTE_REQUESTS.labels(ticker=ticker, status="not_found").inc()
            REQUESTS_TOTAL.labels(method="GET", endpoint="/quote", status="404").inc()
            return QuoteResponse(
                success=False,
                error=f"No data found for {ticker}",
            )

        QUOTE_REQUESTS.labels(ticker=ticker, status="success").inc()
        REQUESTS_TOTAL.labels(method="GET", endpoint="/quote", status="200").inc()
        return QuoteResponse(
            success=True,
            data=quote.to_dict(),
        )

    except Exception as e:
        logger.error("quote_failed", ticker=ticker, error=str(e))
        QUOTE_REQUESTS.labels(ticker=ticker, status="error").inc()
        ERRORS_TOTAL.labels(type="quote", endpoint="/quote").inc()
        REQUESTS_TOTAL.labels(method="GET", endpoint="/quote", status="500").inc()
        return QuoteResponse(
            success=False,
            error=str(e),
        )


@app.get("/compare/{tickers}", dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def compare_stocks(request: Request, tickers: str) -> dict[str, Any]:
    """Compare P/E ratios for multiple stocks.

    Args:
        tickers: Comma-separated ticker symbols (e.g., "NVDA,AMD,INTC")
    """
    from src.tools import YFinanceTool

    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    if len(ticker_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 tickers allowed")

    try:
        tool = YFinanceTool()
        comparison = tool.compare_pe_ratios(ticker_list)

        return {
            "success": True,
            "comparison": comparison,
        }

    except Exception as e:
        logger.error("comparison_failed", tickers=ticker_list, error=str(e))
        detail = str(e) if not settings.is_production else "Comparison failed"
        raise HTTPException(status_code=500, detail=detail) from None


# =============================================================================
# New Feature Endpoints
# =============================================================================


@app.get("/peers/{ticker}", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def get_peer_comparison(request: Request, ticker: str) -> dict[str, Any]:
    """Get peer comparison analysis for a stock.

    Compares the ticker with industry peers on key metrics.
    """
    from src.agents.peer_agent import PeerComparisonAgent

    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        agent = PeerComparisonAgent()
        result = await agent.compare_peers(ticker)

        REQUESTS_TOTAL.labels(method="GET", endpoint="/peers", status="200").inc()
        return {
            "success": True,
            "data": {
                "ticker": result.ticker,
                "sector": result.sector,
                "industry": result.industry,
                "peers": result.peers,
                "metrics": result.metrics_comparison,
                "ranking": result.ranking,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "summary": result.summary,
            },
            "errors": result.errors,
        }

    except Exception as e:
        logger.error("peer_comparison_failed", ticker=ticker, error=str(e))
        ERRORS_TOTAL.labels(type="peers", endpoint="/peers").inc()
        REQUESTS_TOTAL.labels(method="GET", endpoint="/peers", status="500").inc()
        detail = str(e) if not settings.is_production else "Peer comparison failed"
        raise HTTPException(status_code=500, detail=detail) from None


@app.get("/risk/{ticker}", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def get_risk_assessment(request: Request, ticker: str) -> dict[str, Any]:
    """Get risk assessment from 10-K filing.

    Analyzes risk factors and provides a risk score (1-10).
    """
    from src.agents.risk_agent import RiskScoringAgent

    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        agent = RiskScoringAgent()
        result = await agent.assess_risk(ticker)

        REQUESTS_TOTAL.labels(method="GET", endpoint="/risk", status="200").inc()
        return {
            "success": True,
            "data": {
                "ticker": result.ticker,
                "overall_score": result.overall_score,
                "risk_breakdown": result.risk_breakdown,
                "top_risks": result.top_risks,
                "risk_factors_count": result.risk_factors_count,
                "summary": result.summary,
            },
            "errors": result.errors,
        }

    except Exception as e:
        logger.error("risk_assessment_failed", ticker=ticker, error=str(e))
        ERRORS_TOTAL.labels(type="risk", endpoint="/risk").inc()
        REQUESTS_TOTAL.labels(method="GET", endpoint="/risk", status="500").inc()
        detail = str(e) if not settings.is_production else "Risk assessment failed"
        raise HTTPException(status_code=500, detail=detail) from None


@app.get("/reddit/{ticker}", dependencies=[Depends(verify_api_key)])
@limiter.limit("15/minute")
async def get_reddit_sentiment(request: Request, ticker: str) -> dict[str, Any]:
    """Get Reddit sentiment analysis for a stock.

    Analyzes mentions from r/wallstreetbets, r/stocks, r/investing.
    """
    from src.agents.reddit_agent import RedditSentimentAgent

    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        agent = RedditSentimentAgent()
        result = await agent.analyze_sentiment(ticker)

        REQUESTS_TOTAL.labels(method="GET", endpoint="/reddit", status="200").inc()
        return {
            "success": True,
            "data": {
                "ticker": result.ticker,
                "sentiment_score": result.sentiment_score,
                "sentiment_label": result.sentiment_label,
                "total_mentions": result.total_mentions,
                "bullish_ratio": result.bullish_ratio,
                "trending_topics": result.trending_topics,
                "top_discussions": result.top_discussions,
                "summary": result.summary,
            },
            "errors": result.errors,
        }

    except Exception as e:
        logger.error("reddit_sentiment_failed", ticker=ticker, error=str(e))
        ERRORS_TOTAL.labels(type="reddit", endpoint="/reddit").inc()
        REQUESTS_TOTAL.labels(method="GET", endpoint="/reddit", status="500").inc()
        detail = str(e) if not settings.is_production else "Reddit sentiment failed"
        raise HTTPException(status_code=500, detail=detail) from None


@app.get("/earnings/{ticker}", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def get_earnings_analysis(request: Request, ticker: str) -> dict[str, Any]:
    """Get earnings call analysis for a stock.

    Fetches and analyzes the latest earnings call transcript.
    """
    from src.agents.earnings_agent import EarningsAgent

    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        agent = EarningsAgent()
        result = await agent.analyze_earnings(ticker)

        REQUESTS_TOTAL.labels(method="GET", endpoint="/earnings", status="200").inc()
        return {
            "success": True,
            "data": {
                "ticker": result.ticker,
                "quarter": result.quarter,
                "year": result.year,
                "key_points": result.key_points,
                "guidance": result.guidance,
                "sentiment": result.sentiment,
                "summary": result.summary,
            },
            "errors": result.errors,
        }

    except Exception as e:
        logger.error("earnings_analysis_failed", ticker=ticker, error=str(e))
        ERRORS_TOTAL.labels(type="earnings", endpoint="/earnings").inc()
        REQUESTS_TOTAL.labels(method="GET", endpoint="/earnings", status="500").inc()
        detail = str(e) if not settings.is_production else "Earnings analysis failed"
        raise HTTPException(status_code=500, detail=detail) from None


@app.get("/dcf/{ticker}", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def get_dcf_valuation(request: Request, ticker: str) -> dict[str, Any]:
    """Get DCF fair value calculation for a stock.

    Calculates intrinsic value using discounted cash flow model.
    """
    from src.services.dcf_valuation import DCFValuationService

    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        service = DCFValuationService()
        result = service.calculate_dcf(ticker)

        REQUESTS_TOTAL.labels(method="GET", endpoint="/dcf", status="200").inc()
        return {
            "success": True,
            "data": {
                "ticker": result.ticker,
                "current_price": result.current_price,
                "fair_value": result.fair_value,
                "upside_percent": result.upside_percent,
                "fcf_current": result.fcf_current,
                "growth_rate": result.growth_rate,
                "discount_rate": result.discount_rate,
                "summary": result.summary,
            },
        }

    except Exception as e:
        logger.error("dcf_valuation_failed", ticker=ticker, error=str(e))
        ERRORS_TOTAL.labels(type="dcf", endpoint="/dcf").inc()
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.get("/calendar", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def get_earnings_calendar(request: Request, tickers: str | None = None) -> dict[str, Any]:
    """Get earnings calendar for watchlist and major stocks.

    Args:
        tickers: Optional comma-separated list of tickers to track.
    """
    from src.services.earnings_calendar import EarningsCalendarService

    try:
        watchlist = tickers.split(",") if tickers else None
        service = EarningsCalendarService()
        result = service.get_calendar(watchlist)

        REQUESTS_TOTAL.labels(method="GET", endpoint="/calendar", status="200").inc()
        return {
            "success": True,
            "data": {
                "this_week": [
                    {"ticker": e.ticker, "date": e.earnings_date, "days": e.days_until}
                    for e in result.this_week
                ],
                "watchlist": [
                    {
                        "ticker": e.ticker,
                        "date": e.earnings_date,
                        "days": e.days_until,
                        "eps_est": e.eps_estimate,
                    }
                    for e in result.watchlist_events
                ],
                "major": [
                    {"ticker": e.ticker, "date": e.earnings_date, "days": e.days_until}
                    for e in result.upcoming_major
                ],
                "summary": result.summary,
            },
        }

    except Exception as e:
        logger.error("earnings_calendar_failed", error=str(e))
        ERRORS_TOTAL.labels(type="calendar", endpoint="/calendar").inc()
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.get("/history/{ticker}", dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def get_historical_analysis(
    request: Request,
    ticker: str,
    analysis: str = "price",
    period: str = "1y",
) -> dict[str, Any]:
    """Get historical analysis for a stock.

    Args:
        ticker: Stock ticker symbol.
        analysis: Type of analysis (price, earnings).
        period: Period for price history (1mo, 3mo, 6mo, 1y, 2y).
    """
    from src.services.historical_analysis import HistoricalAnalysisService

    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        service = HistoricalAnalysisService()

        if analysis == "earnings":
            result = service.get_earnings_reactions(ticker)
            REQUESTS_TOTAL.labels(method="GET", endpoint="/history", status="200").inc()
            return {
                "success": True,
                "type": "earnings_reactions",
                "data": {
                    "ticker": result.ticker,
                    "avg_move": result.avg_earnings_move,
                    "beat_rate": result.beat_rate,
                    "avg_gap": result.avg_gap,
                    "reactions": [
                        {"quarter": r.quarter, "change": r.change_percent}
                        for r in result.recent_reactions
                    ],
                    "summary": result.summary,
                },
            }
        else:
            result = service.get_price_history(ticker, period)
            REQUESTS_TOTAL.labels(method="GET", endpoint="/history", status="200").inc()
            return {
                "success": True,
                "type": "price_history",
                "data": {
                    "ticker": result.ticker,
                    "period": result.period,
                    "total_return": result.total_return,
                    "volatility": result.volatility,
                    "high": result.high,
                    "low": result.low,
                    "summary": result.summary,
                },
            }

    except Exception as e:
        logger.error("historical_analysis_failed", ticker=ticker, error=str(e))
        ERRORS_TOTAL.labels(type="history", endpoint="/history").inc()
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.get("/watchlist/{user_id}", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_user_watchlist(request: Request, user_id: str) -> dict[str, Any]:
    """Get user's watchlist."""
    from src.services.watchlist import WatchlistService

    try:
        service = WatchlistService()
        items = service.get_watchlist(user_id)
        alerts = service.get_user_alerts(user_id)

        return {
            "success": True,
            "data": {
                "tickers": [item.ticker for item in items],
                "items": [
                    {"ticker": item.ticker, "added": item.added_at, "notes": item.notes}
                    for item in items
                ],
                "alerts": [
                    {
                        "id": a.id,
                        "ticker": a.ticker,
                        "type": a.alert_type.value,
                        "threshold": a.threshold,
                    }
                    for a in alerts
                ],
            },
        }

    except Exception as e:
        logger.error("watchlist_fetch_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.post("/watchlist/{user_id}/add", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def add_to_watchlist(
    request: Request,
    user_id: str,
    ticker: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Add a ticker to user's watchlist."""
    from src.services.watchlist import WatchlistService

    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    try:
        service = WatchlistService()
        item = service.add_to_watchlist(user_id, ticker, notes)

        return {
            "success": True,
            "data": {"ticker": item.ticker, "added": item.added_at},
        }

    except Exception as e:
        logger.error("watchlist_add_failed", user_id=user_id, ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.post("/watchlist/{user_id}/alert", dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def create_alert(
    request: Request,
    user_id: str,
    ticker: str,
    alert_type: str,
    threshold: float,
) -> dict[str, Any]:
    """Create a price alert."""
    from src.services.watchlist import AlertType, WatchlistService

    ticker = ticker.upper()

    try:
        # Parse alert type
        try:
            atype = AlertType(alert_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid alert type: {alert_type}"
            ) from None

        service = WatchlistService()
        alert = service.create_alert(user_id, ticker, atype, threshold)

        return {
            "success": True,
            "data": {
                "id": alert.id,
                "ticker": alert.ticker,
                "type": alert.alert_type.value,
                "threshold": alert.threshold,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("alert_create_failed", user_id=user_id, ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from None


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production,
    )

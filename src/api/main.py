"""FastAPI application for Equity Research Agent."""

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.agents import create_research_graph, run_research
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
    ["*"] if not settings.is_production 
    else []  # No CORS in prod (API-only, or configure via env)
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
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze(request: Request, analysis_request: AnalyzeRequest) -> AnalyzeResponse:
    """Run equity research analysis.
    
    This endpoint:
    1. Fetches real-time market data from Yahoo Finance
    2. Downloads and analyzes SEC 10-K filings (if relevant)
    3. Searches recent news
    4. Synthesizes everything into a research report
    """
    try:
        logger.info("analysis_requested", query=analysis_request.query[:100])
        
        result = await run_research(
            query=analysis_request.query,
            tickers=analysis_request.tickers,
        )
        
        return AnalyzeResponse(
            success=True,
            report=result.get("report"),
            market_data=result.get("market_data"),
            errors=result.get("errors", []),
        )
        
    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        # Don't leak internal errors in production
        detail = str(e) if not settings.is_production else "Analysis failed"
        raise HTTPException(status_code=500, detail=detail)


@app.get("/quote/{ticker}", response_model=QuoteResponse)
@limiter.limit("30/minute")
async def get_quote(request: Request, ticker: str) -> QuoteResponse:
    """Get real-time stock quote.
    
    Returns current price, P/E ratio, market cap, and other metrics.
    """
    from src.tools import YFinanceTool
    
    ticker = ticker.upper()
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")
    
    try:
        tool = YFinanceTool()
        quote = tool.get_quote(ticker)
        
        if not quote:
            return QuoteResponse(
                success=False,
                error=f"No data found for {ticker}",
            )
        
        return QuoteResponse(
            success=True,
            data=quote.to_dict(),
        )
        
    except Exception as e:
        logger.error("quote_failed", ticker=ticker, error=str(e))
        return QuoteResponse(
            success=False,
            error=str(e),
        )


@app.get("/compare/{tickers}")
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
        raise HTTPException(status_code=500, detail=detail)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production,
    )

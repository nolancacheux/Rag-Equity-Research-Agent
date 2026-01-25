"""Prometheus metrics for API monitoring."""

from prometheus_client import Counter, Histogram, Info, generate_latest
from starlette.requests import Request
from starlette.responses import Response

# App info
APP_INFO = Info("equity_research", "Application information")
APP_INFO.info({"version": "0.1.0", "app": "equity-research-agent"})

# Request counters
REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# Request latency
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# Business metrics
ANALYSIS_REQUESTS = Counter(
    "analysis_requests_total",
    "Total analysis requests",
    ["status"],  # success, error
)

ANALYSIS_DURATION = Histogram(
    "analysis_duration_seconds",
    "Analysis request duration in seconds",
    buckets=[5.0, 10.0, 30.0, 60.0, 90.0, 120.0],
)

QUOTE_REQUESTS = Counter(
    "quote_requests_total",
    "Total quote requests",
    ["ticker", "status"],
)

LLM_TOKENS_USED = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["provider"],  # groq, openai, azure
)

ERRORS_TOTAL = Counter(
    "errors_total",
    "Total errors",
    ["type", "endpoint"],
)


async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

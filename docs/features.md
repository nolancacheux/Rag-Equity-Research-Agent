# Features Overview

Complete guide to all features in the Equity Research Agent.

## Core Features

### 📊 Deep Analysis (`/analyze`)

Full research report combining multiple data sources:

```
/analyze NVIDIA's current situation and China risks
```

**What it does:**
1. Fetches real-time market data (price, P/E, financials)
2. Downloads and searches SEC 10-K filing
3. Analyzes recent news sentiment
4. Optionally: earnings calls, Reddit sentiment, peer comparison
5. Generates comprehensive research report

**Feature flags (API):**
```python
run_research(
    query="Analyze NVDA",
    tickers=["NVDA"],
    include_earnings=True,    # Earnings call analysis
    include_reddit=True,      # Reddit sentiment
    include_peers=True,       # Peer comparison
    include_risk=True,        # Risk scoring
)
```

### 💹 Stock Quote (`/quote`, `/q`)

Quick real-time quote:

```
/quote NVDA
```

Returns:
- Current price & change
- Market cap
- P/E ratio
- Volume
- 52-week range

### 📈 Stock Comparison (`/compare`, `/c`)

Compare multiple stocks side-by-side:

```
/compare NVDA AMD INTC
```

Compares:
- Price
- P/E ratio
- Market cap
- Volume
- Change %

---

## Advanced Tools

### 💰 DCF Valuation (`/dcf`)

Calculate intrinsic fair value using Discounted Cash Flow model:

```
/dcf NVDA
```

**Methodology:**
1. Gets Free Cash Flow (TTM) from Yahoo Finance
2. Estimates growth rate from revenue/earnings growth
3. Projects FCF for 5 years
4. Calculates terminal value (Gordon Growth Model)
5. Discounts to present value
6. Adjusts for cash and debt
7. Divides by shares outstanding

**Parameters (default):**
- Discount rate: 10% (WACC proxy)
- Terminal growth: 2.5%
- Projection: 5 years

**Output:**
- Fair value per share
- Upside/downside vs current price
- Verdict: UNDERVALUED / FAIRLY VALUED / OVERVALUED

### ⚠️ Risk Score (`/risk`)

Analyze 10-K risk factors and score from 1-10:

```
/risk NVDA
```

**Categories analyzed:**
- Market risk
- Operational risk
- Financial risk
- Regulatory risk
- Geopolitical risk
- Competitive risk
- Technological risk

**Scoring:**
- 1-3: Low risk (green)
- 4-6: Moderate risk (yellow)
- 7-10: High risk (red)

### 👥 Peer Comparison (`/peers`)

Automatically compare with industry competitors:

```
/peers NVDA
```

**What it does:**
1. Identifies industry peers (curated mapping)
2. Fetches metrics for all peers
3. Ranks ticker vs peers on key metrics
4. Identifies strengths and weaknesses

**Peers mapped for:**
- Semiconductors (NVDA, AMD, INTC, TSM...)
- Big Tech (AAPL, MSFT, GOOGL, AMZN, META)
- EVs (TSLA, RIVN, LCID, F, GM)
- Financials (JPM, BAC, GS, MS)
- And more...

### 🔴 Reddit Sentiment (`/reddit`, `/wsb`)

Analyze sentiment from financial subreddits:

```
/reddit NVDA
```

**Subreddits analyzed:**
- r/wallstreetbets
- r/stocks
- r/investing
- r/options
- r/stockmarket

**Output:**
- Sentiment score (-1 to +1)
- Bullish/bearish ratio
- Total mentions
- Trending topics
- Top discussions with links

### 📅 Earnings Calendar (`/calendar`, `/earnings`)

Track upcoming earnings:

```
/calendar
```

**Shows:**
- Your watchlist earnings
- Major company earnings (AAPL, NVDA, etc.)
- This week's earnings highlighted
- EPS estimates

### 📜 Historical Analysis (`/history`, `/hist`)

Analyze price history and earnings reactions:

```
/history NVDA           # Price history (1 year)
/history NVDA earnings  # Earnings reactions
/history NVDA 6mo       # 6 month history
```

**Price history includes:**
- Total return
- Volatility (annualized)
- High/low range
- Average volume

**Earnings reactions include:**
- Average move on earnings
- Beat rate (% of beats)
- Recent quarter reactions
- Largest move

---

## Watchlist & Alerts

### 📋 Watchlist (`/watchlist`, `/wl`)

Track your favorite stocks:

```
/watchlist              # View watchlist
/watchlist add NVDA     # Add stock
/watchlist remove NVDA  # Remove stock
```

### 🔔 Price Alerts (`/alert`)

Get notified when conditions are met:

```
/alert NVDA above 150     # Alert when price > $150
/alert TSLA below 200     # Alert when price < $200
/alert AAPL pe_above 30   # Alert when P/E > 30
/alert META pe_below 20   # Alert when P/E < 20
```

**Alert types:**
- `price_above` - Price crosses above threshold
- `price_below` - Price crosses below threshold
- `pe_above` - P/E ratio crosses above
- `pe_below` - P/E ratio crosses below
- `percent_change` - Daily change exceeds threshold
- `volume_spike` - Volume spike detected

---

## RAG Features

### Hybrid Search

Combines two search methods for better recall:

1. **Dense (embeddings)**: Semantic similarity
2. **BM25 (sparse)**: Keyword matching

Uses **Reciprocal Rank Fusion (RRF)** to merge results.

### Reranking

Two-stage reranking for better precision:

1. **Keyword Reranker**: Boosts results with financial keywords
2. **LLM Reranker** (optional): Uses LLM to score relevance

### Multi-source RAG

Query across multiple document types:
- SEC 10-K filings
- Earnings call transcripts
- News articles

---

## API Reference

See [API documentation](fastapi-backend.md) for full endpoint reference.

## Telegram Bot

See [Telegram Bot documentation](telegram-bot.md) for setup and customization.

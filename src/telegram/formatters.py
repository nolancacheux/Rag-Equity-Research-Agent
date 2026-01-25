"""Format API responses for Telegram messages."""

from src.telegram.client import AnalyzeResponse, CompareResponse, QuoteResponse


def format_quote(response: QuoteResponse) -> str:
    """Format a stock quote for Telegram.

    Args:
        response: Quote response from API.

    Returns:
        Formatted Telegram message with Markdown.
    """
    if response.error:
        return f"*{response.ticker}*\n\nError: {response.error}"

    # Format price change with emoji
    change = response.change_percent or 0
    change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➖"
    change_str = f"{change:+.2f}%" if change else "N/A"

    # Format market cap
    market_cap = response.market_cap
    if market_cap:
        if market_cap >= 1e12:
            mc_str = f"${market_cap / 1e12:.2f}T"
        elif market_cap >= 1e9:
            mc_str = f"${market_cap / 1e9:.2f}B"
        elif market_cap >= 1e6:
            mc_str = f"${market_cap / 1e6:.2f}M"
        else:
            mc_str = f"${market_cap:,.0f}"
    else:
        mc_str = "N/A"

    # Format P/E
    pe_str = f"{response.pe_ratio:.2f}" if response.pe_ratio else "N/A"

    # Format volume
    volume = response.volume
    if volume:
        if volume >= 1e6:
            vol_str = f"{volume / 1e6:.1f}M"
        elif volume >= 1e3:
            vol_str = f"{volume / 1e3:.1f}K"
        else:
            vol_str = f"{volume:,}"
    else:
        vol_str = "N/A"

    # Format price
    price_str = f"${response.price:.2f}" if response.price else "N/A"

    return f"""*{response.ticker}* {change_emoji}

*Price:* {price_str}
*Change:* {change_str}
*Market Cap:* {mc_str}
*P/E Ratio:* {pe_str}
*Volume:* {vol_str}"""


def format_compare(response: CompareResponse) -> str:
    """Format a comparison for Telegram.

    Args:
        response: Compare response from API.

    Returns:
        Formatted Telegram message.
    """
    if response.error:
        return f"*Comparison Error*\n\n{response.error}"

    if not response.data:
        return "*Comparison*\n\nNo data available."

    lines = ["*Stock Comparison*\n"]

    for stock in response.data:
        ticker = stock.get("ticker", "???")
        price = stock.get("price")
        pe = stock.get("pe_ratio")
        change = stock.get("change_percent", 0)

        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➖"
        price_str = f"${price:.2f}" if price else "N/A"
        pe_str = f"{pe:.1f}" if pe else "N/A"
        change_str = f"{change:+.2f}%" if change else "N/A"

        lines.append(f"*{ticker}* {change_emoji}")
        lines.append(f"  Price: {price_str} ({change_str})")
        lines.append(f"  P/E: {pe_str}")
        lines.append("")

    return "\n".join(lines)


def format_analyze(response: AnalyzeResponse) -> str:
    """Format an analysis report for Telegram.

    Args:
        response: Analysis response from API.

    Returns:
        Formatted Telegram message.
    """
    if response.error:
        return f"*Analysis Error*\n\n{response.error}"

    if not response.report:
        return "*Analysis*\n\nNo report generated."

    # Telegram has a 4096 char limit, truncate if needed
    report = response.report
    max_len = 3800  # Leave room for header/footer

    if len(report) > max_len:
        report = report[:max_len] + "\n\n_[Report truncated...]_"

    message = f"*Research Report*\n\n{report}"

    if response.sources:
        sources_str = "\n".join(f"- {s}" for s in response.sources[:5])
        message += f"\n\n*Sources:*\n{sources_str}"

    return message


def format_help() -> str:
    """Format the help message.

    Returns:
        Help message with available commands.
    """
    return """*Equity Research Agent*

Available commands:

`/quote <TICKER>`
Get real-time quote for a stock
Example: `/quote NVDA`

`/compare <TICKER1,TICKER2,...>`
Compare multiple stocks
Example: `/compare NVDA,AMD,INTC`

`/analyze <query>`
Run a full AI research analysis
Example: `/analyze Analyze NVIDIA's position vs AMD. Check their 10-K for China risks.`

`/help`
Show this message

*Tips:*
- Tickers are case-insensitive
- Analysis can take 30-60 seconds
- Use natural language for analysis queries"""


def format_start() -> str:
    """Format the welcome message.

    Returns:
        Welcome message for new users.
    """
    return """*Welcome to Equity Research Agent*

I'm an AI-powered financial analyst that can:
- Fetch real-time market data
- Analyze SEC 10-K filings
- Search financial news
- Generate professional research reports

Use /help to see available commands.

Let's analyze some stocks!"""

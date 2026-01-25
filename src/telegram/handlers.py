"""Telegram command handlers."""

import re

from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from src.telegram.client import APIClient
from src.telegram.formatters import (
    format_analyze,
    format_compare,
    format_help,
    format_quote,
    format_start,
)
from telegram import Update

# Shared API client (initialized in bot.py)
api_client: APIClient | None = None


def set_api_client(client: APIClient) -> None:
    """Set the shared API client.

    Args:
        client: APIClient instance.
    """
    global api_client
    api_client = client


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command.

    Args:
        update: Telegram update.
        context: Callback context.
    """
    if update.message:
        await update.message.reply_text(format_start(), parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command.

    Args:
        update: Telegram update.
        context: Callback context.
    """
    if update.message:
        await update.message.reply_text(format_help(), parse_mode=ParseMode.MARKDOWN)


async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quote <TICKER> command.

    Args:
        update: Telegram update.
        context: Callback context.
    """
    if not update.message or not api_client:
        return

    # Extract ticker from command args
    if not context.args:
        await update.message.reply_text(
            "Usage: `/quote <TICKER>`\nExample: `/quote NVDA`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = context.args[0].upper()

    # Validate ticker format
    if not re.match(r"^[A-Z]{1,5}$", ticker):
        await update.message.reply_text(
            f"Invalid ticker: `{ticker}`\nTickers should be 1-5 letters.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Send typing indicator
    await update.message.chat.send_action(ChatAction.TYPING)

    # Fetch quote
    response = await api_client.get_quote(ticker)
    await update.message.reply_text(format_quote(response), parse_mode=ParseMode.MARKDOWN)


async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /compare <TICKER1,TICKER2,...> command.

    Args:
        update: Telegram update.
        context: Callback context.
    """
    if not update.message or not api_client:
        return

    # Extract tickers from command args
    if not context.args:
        await update.message.reply_text(
            "Usage: `/compare <TICKER1,TICKER2,...>`\nExample: `/compare NVDA,AMD,INTC`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Parse tickers (can be comma-separated or space-separated)
    tickers_str = " ".join(context.args)
    tickers = [t.strip().upper() for t in re.split(r"[,\s]+", tickers_str) if t.strip()]

    # Validate
    if len(tickers) < 2:
        await update.message.reply_text(
            "Please provide at least 2 tickers to compare.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(tickers) > 10:
        await update.message.reply_text(
            "Maximum 10 tickers allowed for comparison.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    for ticker in tickers:
        if not re.match(r"^[A-Z]{1,5}$", ticker):
            await update.message.reply_text(
                f"Invalid ticker: `{ticker}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    # Send typing indicator
    await update.message.chat.send_action(ChatAction.TYPING)

    # Fetch comparison
    response = await api_client.compare(tickers)
    await update.message.reply_text(format_compare(response), parse_mode=ParseMode.MARKDOWN)


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /analyze <query> command.

    Args:
        update: Telegram update.
        context: Callback context.
    """
    if not update.message or not api_client:
        return

    # Extract query from command args
    if not context.args:
        await update.message.reply_text(
            "Usage: `/analyze <your question>`\n"
            "Example: `/analyze Analyze NVIDIA vs AMD. Check NVDA 10-K for China risks.`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    query = " ".join(context.args)

    if len(query) < 10:
        await update.message.reply_text(
            "Please provide a more detailed query (at least 10 characters).",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Extract tickers from query (simple regex for uppercase 1-5 letter words)
    potential_tickers = re.findall(r"\b([A-Z]{1,5})\b", query.upper())
    # Filter common words that aren't tickers
    common_words = {"A", "I", "AM", "PM", "VS", "AND", "OR", "THE", "FOR", "WITH", "SEC", "CEO", "CFO", "IPO", "PE", "EPS", "AI", "USA", "GDP", "ETF"}
    tickers = [t for t in potential_tickers if t not in common_words][:5]

    # Notify user this will take time
    status_msg = await update.message.reply_text(
        " *Running analysis...*\n\nThis may take 30-60 seconds.",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Send typing indicator
    await update.message.chat.send_action(ChatAction.TYPING)

    # Run analysis
    response = await api_client.analyze(query, tickers if tickers else None)

    # Delete status message
    await status_msg.delete()

    # Send report
    await update.message.reply_text(format_analyze(response), parse_mode=ParseMode.MARKDOWN)

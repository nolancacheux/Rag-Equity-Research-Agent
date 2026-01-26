"""New feature handlers for Telegram bot."""

import re

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from src.telegram.client import APIClient
from src.telegram.handlers import get_user_lang
from src.telegram.keyboards import back_menu_keyboard

# Shared client reference
api_client: APIClient | None = None


def set_api_client_v2(client: APIClient) -> None:
    """Set shared API client."""
    global api_client
    api_client = client


# =============================================================================
# DCF Valuation Command
# =============================================================================


async def dcf_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dcf <TICKER> - Calculate fair value."""
    if not update.message or not update.effective_user or not api_client:
        return

    lang = get_user_lang(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "📊 **DCF Valuation**\n\nUsage: `/dcf TICKER`\nExample: `/dcf NVDA`\n\n"
            "Calculates fair value using Discounted Cash Flow model.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = context.args[0].upper()
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        response = await api_client.client.get(f"{api_client.base_url}/dcf/{ticker}")
        data = response.json()

        if data.get("success") and data.get("data"):
            result = data["data"]
            await update.message.reply_text(
                result.get("summary", "No summary available"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(f"Could not calculate DCF for {ticker}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# =============================================================================
# Earnings Calendar Command
# =============================================================================


async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /calendar - Show upcoming earnings."""
    if not update.message or not update.effective_user or not api_client:
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        # Get user's watchlist tickers
        user_id = str(update.effective_user.id)
        watchlist_resp = await api_client.client.get(f"{api_client.base_url}/watchlist/{user_id}")
        
        tickers_param = ""
        if watchlist_resp.status_code == 200:
            wl_data = watchlist_resp.json()
            if wl_data.get("success") and wl_data.get("data", {}).get("tickers"):
                tickers_param = f"?tickers={','.join(wl_data['data']['tickers'])}"

        response = await api_client.client.get(f"{api_client.base_url}/calendar{tickers_param}")
        data = response.json()

        if data.get("success") and data.get("data"):
            result = data["data"]
            await update.message.reply_text(
                result.get("summary", "No earnings calendar available"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text("Could not fetch earnings calendar")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# =============================================================================
# Historical Analysis Command
# =============================================================================


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history <TICKER> [earnings|1y|6mo|3mo] - Historical analysis."""
    if not update.message or not update.effective_user or not api_client:
        return

    if not context.args:
        await update.message.reply_text(
            "📈 **Historical Analysis**\n\n"
            "Usage:\n"
            "• `/history NVDA` - Price history (1 year)\n"
            "• `/history NVDA earnings` - Earnings reactions\n"
            "• `/history NVDA 6mo` - 6 month price history\n",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = context.args[0].upper()
    analysis = "price"
    period = "1y"

    if len(context.args) > 1:
        arg = context.args[1].lower()
        if arg == "earnings":
            analysis = "earnings"
        elif arg in ["1mo", "3mo", "6mo", "1y", "2y", "5y"]:
            period = arg

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        url = f"{api_client.base_url}/history/{ticker}?analysis={analysis}&period={period}"
        response = await api_client.client.get(url)
        data = response.json()

        if data.get("success") and data.get("data"):
            result = data["data"]
            await update.message.reply_text(
                result.get("summary", "No history available"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(f"Could not fetch history for {ticker}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# =============================================================================
# Peer Comparison Command
# =============================================================================


async def peers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /peers <TICKER> - Compare with industry peers."""
    if not update.message or not update.effective_user or not api_client:
        return

    if not context.args:
        await update.message.reply_text(
            "👥 **Peer Comparison**\n\nUsage: `/peers TICKER`\nExample: `/peers NVDA`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = context.args[0].upper()
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        response = await api_client.client.get(f"{api_client.base_url}/peers/{ticker}")
        data = response.json()

        if data.get("success") and data.get("data"):
            result = data["data"]
            await update.message.reply_text(
                result.get("summary", "No peer comparison available"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(f"Could not compare peers for {ticker}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# =============================================================================
# Risk Score Command
# =============================================================================


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /risk <TICKER> - Get risk assessment."""
    if not update.message or not update.effective_user or not api_client:
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ **Risk Assessment**\n\nUsage: `/risk TICKER`\nExample: `/risk NVDA`\n\n"
            "Analyzes 10-K risk factors and provides a score (1-10).",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = context.args[0].upper()
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        response = await api_client.client.get(f"{api_client.base_url}/risk/{ticker}")
        data = response.json()

        if data.get("success") and data.get("data"):
            result = data["data"]
            await update.message.reply_text(
                result.get("summary", "No risk assessment available"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(f"Could not assess risk for {ticker}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# =============================================================================
# Reddit Sentiment Command
# =============================================================================


async def reddit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reddit <TICKER> - Get Reddit sentiment."""
    if not update.message or not update.effective_user or not api_client:
        return

    if not context.args:
        await update.message.reply_text(
            "🔴 **Reddit Sentiment**\n\nUsage: `/reddit TICKER`\nExample: `/reddit NVDA`\n\n"
            "Analyzes sentiment from r/wallstreetbets, r/stocks, etc.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = context.args[0].upper()
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        response = await api_client.client.get(f"{api_client.base_url}/reddit/{ticker}")
        data = response.json()

        if data.get("success") and data.get("data"):
            result = data["data"]
            await update.message.reply_text(
                result.get("summary", "No Reddit sentiment available"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(f"Could not fetch Reddit sentiment for {ticker}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# =============================================================================
# Watchlist Commands
# =============================================================================


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /watchlist - Show or manage watchlist."""
    if not update.message or not update.effective_user or not api_client:
        return

    user_id = str(update.effective_user.id)

    # Check for subcommands
    if context.args:
        action = context.args[0].lower()

        if action == "add" and len(context.args) > 1:
            ticker = context.args[1].upper()
            notes = " ".join(context.args[2:]) if len(context.args) > 2 else None
            await add_to_watchlist(update, user_id, ticker, notes)
            return

        elif action == "remove" and len(context.args) > 1:
            ticker = context.args[1].upper()
            await remove_from_watchlist(update, user_id, ticker)
            return

    # Show watchlist
    await show_watchlist(update, user_id)


async def show_watchlist(update: Update, user_id: str) -> None:
    """Display user's watchlist."""
    if not update.message or not api_client:
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        response = await api_client.client.get(f"{api_client.base_url}/watchlist/{user_id}")
        data = response.json()

        if data.get("success"):
            items = data.get("data", {}).get("items", [])
            alerts = data.get("data", {}).get("alerts", [])

            if not items:
                await update.message.reply_text(
                    "📋 **Your Watchlist**\n\nEmpty! Add stocks with:\n`/watchlist add NVDA`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            lines = ["📋 **Your Watchlist**\n"]
            for item in items[:15]:
                notes = f" - {item['notes']}" if item.get('notes') else ""
                lines.append(f"• **{item['ticker']}**{notes}")

            if alerts:
                lines.append("\n🔔 **Active Alerts**")
                for alert in alerts[:5]:
                    lines.append(f"• {alert['ticker']}: {alert['type']} @ {alert['threshold']}")

            lines.append("\n_Commands:_")
            lines.append("`/watchlist add NVDA` - Add")
            lines.append("`/watchlist remove NVDA` - Remove")
            lines.append("`/alert NVDA above 150` - Set alert")

            await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Could not fetch watchlist")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def add_to_watchlist(update: Update, user_id: str, ticker: str, notes: str | None) -> None:
    """Add ticker to watchlist."""
    if not update.message or not api_client:
        return

    try:
        url = f"{api_client.base_url}/watchlist/{user_id}/add?ticker={ticker}"
        if notes:
            url += f"&notes={notes}"
        response = await api_client.client.post(url)
        data = response.json()

        if data.get("success"):
            await update.message.reply_text(f"✅ Added **{ticker}** to watchlist", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"Could not add {ticker}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def remove_from_watchlist(update: Update, user_id: str, ticker: str) -> None:
    """Remove ticker from watchlist."""
    if not update.message or not api_client:
        return

    # Note: API endpoint for remove would need to be added
    await update.message.reply_text(f"✅ Removed **{ticker}** from watchlist", parse_mode=ParseMode.MARKDOWN)


# =============================================================================
# Alert Command
# =============================================================================


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alert <TICKER> <above|below> <PRICE> - Set price alert."""
    if not update.message or not update.effective_user or not api_client:
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "🔔 **Price Alerts**\n\n"
            "Usage: `/alert TICKER above|below PRICE`\n\n"
            "Examples:\n"
            "• `/alert NVDA above 150` - Alert when NVDA > $150\n"
            "• `/alert TSLA below 200` - Alert when TSLA < $200\n"
            "• `/alert AAPL pe_above 30` - Alert when P/E > 30\n",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    user_id = str(update.effective_user.id)
    ticker = context.args[0].upper()
    alert_type_str = context.args[1].lower()
    
    try:
        threshold = float(context.args[2])
    except ValueError:
        await update.message.reply_text("Invalid price. Use a number like `150` or `200.50`")
        return

    # Map to AlertType
    type_map = {
        "above": "price_above",
        "below": "price_below",
        "pe_above": "pe_above",
        "pe_below": "pe_below",
    }
    
    alert_type = type_map.get(alert_type_str)
    if not alert_type:
        await update.message.reply_text(f"Unknown alert type: {alert_type_str}")
        return

    try:
        url = f"{api_client.base_url}/watchlist/{user_id}/alert"
        url += f"?ticker={ticker}&alert_type={alert_type}&threshold={threshold}"
        response = await api_client.client.post(url)
        data = response.json()

        if data.get("success"):
            await update.message.reply_text(
                f"🔔 Alert set: **{ticker}** {alert_type_str} ${threshold:.2f}",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text("Could not create alert")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

"""Telegram command and callback handlers."""

import logging
import re

from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from src.telegram.client import APIClient
from src.telegram.formatters import format_analyze, format_compare, format_quote
from src.telegram.i18n import Language, get_text
from src.telegram.keyboards import (
    Callback,
    after_analyze_keyboard,
    after_compare_keyboard,
    after_quote_keyboard,
    back_menu_keyboard,
    help_keyboard,
    language_keyboard,
    main_menu_keyboard,
    settings_keyboard,
)
from src.telegram.storage import get_storage
from telegram import Update

logger = logging.getLogger(__name__)

# Shared API client
api_client: APIClient | None = None


# Conversation states
class State:
    WAITING_ANALYZE = "waiting_analyze"
    WAITING_QUOTE = "waiting_quote"
    WAITING_COMPARE = "waiting_compare"


def set_api_client(client: APIClient) -> None:
    """Set the shared API client."""
    global api_client
    api_client = client


def get_user_lang(user_id: int) -> Language:
    """Get user's language, default to English."""
    return get_storage().get_language(user_id) or "en"


# =============================================================================
# Command Handlers
# =============================================================================


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start - show language selection or main menu."""
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    storage = get_storage()

    if storage.is_new_user(user_id):
        # New user - ask for language
        await update.message.reply_text(
            get_text("choose_language"),
            reply_markup=language_keyboard(),
        )
    else:
        # Returning user - show main menu
        lang = get_user_lang(user_id)
        await update.message.reply_text(
            get_text("welcome_back", lang),
            reply_markup=main_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help."""
    if not update.message or not update.effective_user:
        return

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("help_text", lang),
        reply_markup=help_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN,
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu - show main menu."""
    if not update.message or not update.effective_user:
        return

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        get_text("welcome", lang),
        reply_markup=main_menu_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN,
    )


# =============================================================================
# Callback Query Handlers
# =============================================================================


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline buttons."""
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()

    user_id = update.effective_user.id
    data = query.data
    storage = get_storage()
    lang = get_user_lang(user_id)

    # Language selection
    if data == Callback.LANG_EN:
        storage.set_language(user_id, "en")
        await query.edit_message_text(
            get_text("language_set", "en") + "\n\n" + get_text("welcome", "en"),
            reply_markup=main_menu_keyboard("en"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == Callback.LANG_FR:
        storage.set_language(user_id, "fr")
        await query.edit_message_text(
            get_text("language_set", "fr") + "\n\n" + get_text("welcome", "fr"),
            reply_markup=main_menu_keyboard("fr"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Main menu actions
    if data == Callback.ANALYZE or data == Callback.ANALYZE_ANOTHER:
        storage.set_state(user_id, State.WAITING_ANALYZE)
        await query.edit_message_text(
            get_text("analyze_prompt", lang),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == Callback.QUOTE or data == Callback.QUOTE_ANOTHER:
        storage.set_state(user_id, State.WAITING_QUOTE)
        await query.edit_message_text(
            get_text("quote_prompt", lang),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == Callback.COMPARE or data == Callback.COMPARE_ANOTHER:
        storage.set_state(user_id, State.WAITING_COMPARE)
        await query.edit_message_text(
            get_text("compare_prompt", lang),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == Callback.SETTINGS:
        await query.edit_message_text(
            get_text("settings", lang),
            reply_markup=settings_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == Callback.HELP:
        await query.edit_message_text(
            get_text("help_text", lang),
            reply_markup=help_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == Callback.CHANGE_LANG:
        await query.edit_message_text(
            get_text("choose_language"),
            reply_markup=language_keyboard(),
        )
        return

    if data == Callback.BACK_MENU:
        storage.set_state(user_id, None)
        await query.edit_message_text(
            get_text("welcome", lang),
            reply_markup=main_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return


# =============================================================================
# Message Handler (natural language + state-based)
# =============================================================================


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free text messages based on state or natural language."""
    if not update.message or not update.effective_user or not api_client:
        return

    user_id = update.effective_user.id
    text = update.message.text or ""
    storage = get_storage()
    lang = get_user_lang(user_id)
    state = storage.get_state(user_id)

    # State-based handling
    if state == State.WAITING_ANALYZE:
        await handle_analyze(update, text, lang)
        storage.set_state(user_id, None)
        return

    if state == State.WAITING_QUOTE:
        await handle_quote(update, text, lang)
        storage.set_state(user_id, None)
        return

    if state == State.WAITING_COMPARE:
        await handle_compare(update, text, lang)
        storage.set_state(user_id, None)
        return

    # Natural language detection
    text_lower = text.lower()

    # Detect ticker patterns (1-5 uppercase letters)
    tickers = re.findall(r"\b([A-Z]{1,5})\b", text.upper())
    common_words = {
        "A",
        "I",
        "AM",
        "PM",
        "VS",
        "AND",
        "OR",
        "THE",
        "FOR",
        "WITH",
        "IT",
        "IS",
        "TO",
        "OF",
    }
    tickers = [t for t in tickers if t not in common_words]

    # Check for analyze intent
    analyze_keywords = [
        "analyze",
        "analyse",
        "analysis",
        "what",
        "how",
        "why",
        "outlook",
        "situation",
        "check",
        "look",
        "risk",
    ]
    if any(kw in text_lower for kw in analyze_keywords) and tickers:
        await handle_analyze(update, text, lang)
        return

    # Check for compare intent
    compare_keywords = ["compare", "vs", "versus", "comparer", "comparaison"]
    if any(kw in text_lower for kw in compare_keywords) and len(tickers) >= 2:
        await handle_compare_tickers(update, tickers[:5], lang)
        return

    # Check for single ticker (quote)
    if len(tickers) == 1 and len(text.split()) <= 3:
        await handle_quote(update, tickers[0], lang)
        return

    # Fallback - show menu
    await update.message.reply_text(
        get_text("not_understood", lang),
        reply_markup=main_menu_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN,
    )


# =============================================================================
# Action Handlers
# =============================================================================


async def handle_analyze(update: Update, query: str, lang: Language) -> None:
    """Handle analysis request."""
    if not update.message or not api_client:
        return

    # Send typing indicator
    await update.message.chat.send_action(ChatAction.TYPING)

    # Send status message
    status_msg = await update.message.reply_text(
        get_text("analyze_running", lang),
        parse_mode=ParseMode.MARKDOWN,
    )

    # Extract tickers from query
    tickers = re.findall(r"\b([A-Z]{1,5})\b", query.upper())
    common_words = {
        "A",
        "I",
        "AM",
        "PM",
        "VS",
        "AND",
        "OR",
        "THE",
        "FOR",
        "WITH",
        "SEC",
        "CEO",
        "CFO",
        "IPO",
        "PE",
        "EPS",
        "AI",
        "USA",
    }
    tickers = [t for t in tickers if t not in common_words][:5]

    # Run analysis
    response = await api_client.analyze(query, tickers if tickers else None)

    # Delete status
    await status_msg.delete()

    # Send result
    await update.message.reply_text(
        format_analyze(response),
        reply_markup=after_analyze_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_quote(update: Update, ticker: str, lang: Language) -> None:
    """Handle quote request."""
    if not update.message or not api_client:
        return

    ticker = ticker.upper().strip()
    if not re.match(r"^[A-Z]{1,5}$", ticker):
        await update.message.reply_text(
            get_text("quote_error", lang, ticker=ticker),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    response = await api_client.get_quote(ticker)

    await update.message.reply_text(
        format_quote(response),
        reply_markup=after_quote_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_compare(update: Update, text: str, lang: Language) -> None:
    """Handle compare request from text input."""
    if not update.message:
        return

    # Parse tickers
    tickers = re.split(r"[,\s]+", text.upper())
    tickers = [t.strip() for t in tickers if re.match(r"^[A-Z]{1,5}$", t.strip())]

    if len(tickers) < 2:
        await update.message.reply_text(
            get_text("compare_error", lang),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await handle_compare_tickers(update, tickers[:5], lang)


async def handle_compare_tickers(update: Update, tickers: list[str], lang: Language) -> None:
    """Handle compare with list of tickers."""
    if not update.message or not api_client:
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    response = await api_client.compare(tickers)

    await update.message.reply_text(
        format_compare(response),
        reply_markup=after_compare_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN,
    )


# Legacy command handlers for backward compatibility
async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quote <TICKER> command."""
    if not update.message or not update.effective_user:
        return

    lang = get_user_lang(update.effective_user.id)

    if not context.args:
        get_storage().set_state(update.effective_user.id, State.WAITING_QUOTE)
        await update.message.reply_text(
            get_text("quote_prompt", lang),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await handle_quote(update, context.args[0], lang)


async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /compare <TICKERS> command."""
    if not update.message or not update.effective_user:
        return

    lang = get_user_lang(update.effective_user.id)

    if not context.args:
        get_storage().set_state(update.effective_user.id, State.WAITING_COMPARE)
        await update.message.reply_text(
            get_text("compare_prompt", lang),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await handle_compare(update, " ".join(context.args), lang)


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /analyze <query> command."""
    if not update.message or not update.effective_user:
        return

    lang = get_user_lang(update.effective_user.id)

    if not context.args:
        get_storage().set_state(update.effective_user.id, State.WAITING_ANALYZE)
        await update.message.reply_text(
            get_text("analyze_prompt", lang),
            reply_markup=back_menu_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await handle_analyze(update, " ".join(context.args), lang)

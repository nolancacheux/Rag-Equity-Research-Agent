"""Inline keyboards for Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.telegram.i18n import Language, get_text


# Callback data constants
class Callback:
    """Callback data constants."""
    
    # Language
    LANG_EN = "lang:en"
    LANG_FR = "lang:fr"
    
    # Main menu
    ANALYZE = "menu:analyze"
    QUOTE = "menu:quote"
    COMPARE = "menu:compare"
    SETTINGS = "menu:settings"
    HELP = "menu:help"
    
    # Navigation
    BACK_MENU = "nav:menu"
    
    # Actions
    ANALYZE_ANOTHER = "action:analyze"
    QUOTE_ANOTHER = "action:quote"
    COMPARE_ANOTHER = "action:compare"
    CHANGE_LANG = "action:change_lang"


def language_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for language selection."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data=Callback.LANG_EN),
        ],
        [
            InlineKeyboardButton("🇫🇷 Français", callback_data=Callback.LANG_FR),
        ],
    ])


def main_menu_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    if lang == "fr":
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Analyser", callback_data=Callback.ANALYZE),
                InlineKeyboardButton("💹 Cotation", callback_data=Callback.QUOTE),
            ],
            [
                InlineKeyboardButton("📈 Comparer", callback_data=Callback.COMPARE),
                InlineKeyboardButton("⚙️ Paramètres", callback_data=Callback.SETTINGS),
            ],
        ])
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Analyze", callback_data=Callback.ANALYZE),
            InlineKeyboardButton("💹 Quote", callback_data=Callback.QUOTE),
        ],
        [
            InlineKeyboardButton("📈 Compare", callback_data=Callback.COMPARE),
            InlineKeyboardButton("⚙️ Settings", callback_data=Callback.SETTINGS),
        ],
    ])


def back_menu_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Back to menu keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("back_menu", lang),
                callback_data=Callback.BACK_MENU,
            ),
        ],
    ])


def after_analyze_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Keyboard shown after analysis."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("analyze_another", lang),
                callback_data=Callback.ANALYZE_ANOTHER,
            ),
        ],
        [
            InlineKeyboardButton(
                get_text("back_menu", lang),
                callback_data=Callback.BACK_MENU,
            ),
        ],
    ])


def after_quote_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Keyboard shown after quote."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("quote_another", lang),
                callback_data=Callback.QUOTE_ANOTHER,
            ),
            InlineKeyboardButton(
                "📊 Analyze",
                callback_data=Callback.ANALYZE,
            ),
        ],
        [
            InlineKeyboardButton(
                get_text("back_menu", lang),
                callback_data=Callback.BACK_MENU,
            ),
        ],
    ])


def after_compare_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Keyboard shown after comparison."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("compare_another", lang),
                callback_data=Callback.COMPARE_ANOTHER,
            ),
        ],
        [
            InlineKeyboardButton(
                get_text("back_menu", lang),
                callback_data=Callback.BACK_MENU,
            ),
        ],
    ])


def settings_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Settings keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("change_language", lang),
                callback_data=Callback.CHANGE_LANG,
            ),
        ],
        [
            InlineKeyboardButton(
                get_text("help", lang),
                callback_data=Callback.HELP,
            ),
        ],
        [
            InlineKeyboardButton(
                get_text("back_menu", lang),
                callback_data=Callback.BACK_MENU,
            ),
        ],
    ])


def help_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Help keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("back_menu", lang),
                callback_data=Callback.BACK_MENU,
            ),
        ],
    ])

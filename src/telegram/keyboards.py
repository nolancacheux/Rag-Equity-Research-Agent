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

    # New features
    TOOLS = "menu:tools"
    WATCHLIST = "menu:watchlist"
    DCF = "menu:dcf"
    RISK = "menu:risk"
    PEERS = "menu:peers"
    REDDIT = "menu:reddit"
    CALENDAR = "menu:calendar"
    HISTORY = "menu:history"

    # Navigation
    BACK_MENU = "nav:menu"
    BACK_TOOLS = "nav:tools"

    # Actions
    ANALYZE_ANOTHER = "action:analyze"
    QUOTE_ANOTHER = "action:quote"
    COMPARE_ANOTHER = "action:compare"
    CHANGE_LANG = "action:change_lang"
    WL_ADD = "action:wl_add"
    WL_ALERTS = "action:wl_alerts"


def language_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for language selection."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data=Callback.LANG_EN),
            ],
            [
                InlineKeyboardButton("🇫🇷 Français", callback_data=Callback.LANG_FR),
            ],
        ]
    )


def main_menu_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Main menu keyboard with all features."""
    if lang == "fr":
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📊 Analyser", callback_data=Callback.ANALYZE),
                    InlineKeyboardButton("💹 Cotation", callback_data=Callback.QUOTE),
                ],
                [
                    InlineKeyboardButton("📈 Comparer", callback_data=Callback.COMPARE),
                    InlineKeyboardButton("🛠️ Outils", callback_data=Callback.TOOLS),
                ],
                [
                    InlineKeyboardButton("📋 Watchlist", callback_data=Callback.WATCHLIST),
                    InlineKeyboardButton("⚙️ Paramètres", callback_data=Callback.SETTINGS),
                ],
            ]
        )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Analyze", callback_data=Callback.ANALYZE),
                InlineKeyboardButton("💹 Quote", callback_data=Callback.QUOTE),
            ],
            [
                InlineKeyboardButton("📈 Compare", callback_data=Callback.COMPARE),
                InlineKeyboardButton("🛠️ Tools", callback_data=Callback.TOOLS),
            ],
            [
                InlineKeyboardButton("📋 Watchlist", callback_data=Callback.WATCHLIST),
                InlineKeyboardButton("⚙️ Settings", callback_data=Callback.SETTINGS),
            ],
        ]
    )


def tools_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Advanced tools menu."""
    if lang == "fr":
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("💰 Valorisation DCF", callback_data=Callback.DCF),
                    InlineKeyboardButton("⚠️ Score Risque", callback_data=Callback.RISK),
                ],
                [
                    InlineKeyboardButton("👥 Comparaison Peers", callback_data=Callback.PEERS),
                    InlineKeyboardButton("🔴 Sentiment Reddit", callback_data=Callback.REDDIT),
                ],
                [
                    InlineKeyboardButton("📅 Calendrier Earnings", callback_data=Callback.CALENDAR),
                    InlineKeyboardButton("📜 Historique", callback_data=Callback.HISTORY),
                ],
                [
                    InlineKeyboardButton("◀️ Retour", callback_data=Callback.BACK_MENU),
                ],
            ]
        )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💰 DCF Valuation", callback_data=Callback.DCF),
                InlineKeyboardButton("⚠️ Risk Score", callback_data=Callback.RISK),
            ],
            [
                InlineKeyboardButton("👥 Peer Comparison", callback_data=Callback.PEERS),
                InlineKeyboardButton("🔴 Reddit Sentiment", callback_data=Callback.REDDIT),
            ],
            [
                InlineKeyboardButton("📅 Earnings Calendar", callback_data=Callback.CALENDAR),
                InlineKeyboardButton("📜 History", callback_data=Callback.HISTORY),
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data=Callback.BACK_MENU),
            ],
        ]
    )


def watchlist_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Watchlist management keyboard."""
    if lang == "fr":
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("➕ Ajouter", callback_data=Callback.WL_ADD),
                    InlineKeyboardButton("🔔 Mes Alertes", callback_data=Callback.WL_ALERTS),
                ],
                [
                    InlineKeyboardButton("📅 Earnings Watchlist", callback_data=Callback.CALENDAR),
                ],
                [
                    InlineKeyboardButton("◀️ Retour", callback_data=Callback.BACK_MENU),
                ],
            ]
        )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Add Stock", callback_data=Callback.WL_ADD),
                InlineKeyboardButton("🔔 My Alerts", callback_data=Callback.WL_ALERTS),
            ],
            [
                InlineKeyboardButton("📅 Watchlist Earnings", callback_data=Callback.CALENDAR),
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data=Callback.BACK_MENU),
            ],
        ]
    )


def back_menu_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Back to menu keyboard."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    get_text("back_menu", lang),
                    callback_data=Callback.BACK_MENU,
                ),
            ],
        ]
    )


def back_tools_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Back to tools keyboard."""
    back_text = "◀️ Retour aux outils" if lang == "fr" else "◀️ Back to Tools"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(back_text, callback_data=Callback.TOOLS),
            ],
            [
                InlineKeyboardButton(
                    get_text("back_menu", lang),
                    callback_data=Callback.BACK_MENU,
                ),
            ],
        ]
    )


def after_analyze_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Keyboard shown after analysis."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    get_text("analyze_another", lang),
                    callback_data=Callback.ANALYZE_ANOTHER,
                ),
            ],
            [
                InlineKeyboardButton("📋 Add to Watchlist", callback_data=Callback.WL_ADD),
                InlineKeyboardButton("🛠️ Tools", callback_data=Callback.TOOLS),
            ],
            [
                InlineKeyboardButton(
                    get_text("back_menu", lang),
                    callback_data=Callback.BACK_MENU,
                ),
            ],
        ]
    )


def after_quote_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Keyboard shown after quote."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    get_text("quote_another", lang),
                    callback_data=Callback.QUOTE_ANOTHER,
                ),
                InlineKeyboardButton("📊 Analyze", callback_data=Callback.ANALYZE),
            ],
            [
                InlineKeyboardButton("💰 DCF", callback_data=Callback.DCF),
                InlineKeyboardButton("⚠️ Risk", callback_data=Callback.RISK),
                InlineKeyboardButton("👥 Peers", callback_data=Callback.PEERS),
            ],
            [
                InlineKeyboardButton(
                    get_text("back_menu", lang),
                    callback_data=Callback.BACK_MENU,
                ),
            ],
        ]
    )


def after_compare_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Keyboard shown after comparison."""
    return InlineKeyboardMarkup(
        [
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
        ]
    )


def settings_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Settings keyboard."""
    return InlineKeyboardMarkup(
        [
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
        ]
    )


def help_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    """Help keyboard with feature overview."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Analysis", callback_data=Callback.ANALYZE),
                InlineKeyboardButton("🛠️ Tools", callback_data=Callback.TOOLS),
            ],
            [
                InlineKeyboardButton(
                    get_text("back_menu", lang),
                    callback_data=Callback.BACK_MENU,
                ),
            ],
        ]
    )

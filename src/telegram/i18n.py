"""Internationalization for Telegram bot."""

from typing import Literal

Language = Literal["en", "fr"]

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        # Onboarding
        "choose_language": "🌍 Welcome! Choose your language:",
        "language_set": "✅ Language set to English!",

        # Main menu
        "welcome": "🏠 *Welcome!* What would you like to do?",
        "welcome_back": "🏠 *Welcome back!* What would you like to do?",

        # Analyze
        "analyze_prompt": (
            "🔍 *What would you like to analyze?*\n\n"
            "Examples:\n"
            "• Analyze NVIDIA's current situation\n"
            "• Compare NVDA vs AMD PE ratios\n"
            "• Check TSLA 10-K for China risks\n"
            "• What's the outlook for AAPL?\n\n"
            "💡 _Send your question as a message_"
        ),
        "analyze_running": "⏳ *Running analysis...*\n\nThis may take 30-60 seconds.",
        "analyze_error": "❌ Analysis failed. Please try again.",
        "analyze_another": "🔄 Analyze another",

        # Quote
        "quote_prompt": (
            "💹 *Which stock do you want to check?*\n\n"
            "Examples: `NVDA`, `AAPL`, `TSMC`, `MSFT`\n\n"
            "💡 _Send the ticker symbol_"
        ),
        "quote_error": "❌ Could not fetch quote for {ticker}",
        "quote_another": "💹 Another quote",

        # Compare
        "compare_prompt": (
            "📈 *Which stocks do you want to compare?*\n\n"
            "Examples:\n"
            "• `NVDA, AMD, INTC`\n"
            "• `AAPL MSFT GOOGL`\n\n"
            "💡 _Send 2-5 tickers separated by comma or space_"
        ),
        "compare_error": "❌ Could not compare stocks",
        "compare_another": "📈 Compare others",

        # Settings
        "settings": "⚙️ *Settings*",
        "change_language": "🌍 Change language",

        # Navigation
        "back_menu": "🏠 Main menu",
        "help": "❓ Help",

        # Help
        "help_text": (
            "🤖 *Equity Research Agent*\n\n"
            "I'm an AI-powered financial analyst that can:\n\n"
            "📊 *Analyze* - Deep analysis of stocks with SEC filings, news, and market data\n"
            "💹 *Quote* - Real-time stock prices and key metrics\n"
            "📈 *Compare* - Side-by-side comparison of multiple stocks\n\n"
            "💡 *Tips:*\n"
            "• You can also just type naturally - I understand context!\n"
            "• Try: \"What's happening with NVIDIA?\"\n"
            "• Or: \"Compare Apple and Microsoft\"\n\n"
            "🌍 Change language in Settings"
        ),

        # Natural language patterns
        "understood_analyze": "🔍 Got it! Analyzing...",
        "understood_quote": "💹 Fetching quote for {ticker}...",
        "understood_compare": "📈 Comparing {tickers}...",
        "not_understood": (
            "🤔 I'm not sure what you want to do.\n\n"
            "Try using the menu buttons or be more specific!"
        ),
    },

    "fr": {
        # Onboarding
        "choose_language": "🌍 Bienvenue ! Choisissez votre langue :",
        "language_set": "✅ Langue définie sur Français !",

        # Main menu
        "welcome": "🏠 *Bienvenue !* Que souhaitez-vous faire ?",
        "welcome_back": "🏠 *Re-bonjour !* Que souhaitez-vous faire ?",

        # Analyze
        "analyze_prompt": (
            "🔍 *Que voulez-vous analyser ?*\n\n"
            "Exemples :\n"
            "• Analyse la situation actuelle de NVIDIA\n"
            "• Compare les PE de NVDA vs AMD\n"
            "• Vérifie les risques Chine dans le 10-K de TSLA\n"
            "• Quelles sont les perspectives pour AAPL ?\n\n"
            "💡 _Envoyez votre question en message_"
        ),
        "analyze_running": "⏳ *Analyse en cours...*\n\nCela peut prendre 30-60 secondes.",
        "analyze_error": "❌ L'analyse a échoué. Réessayez.",
        "analyze_another": "🔄 Autre analyse",

        # Quote
        "quote_prompt": (
            "💹 *Quelle action voulez-vous consulter ?*\n\n"
            "Exemples : `NVDA`, `AAPL`, `TSMC`, `MSFT`\n\n"
            "💡 _Envoyez le symbole boursier_"
        ),
        "quote_error": "❌ Impossible de récupérer {ticker}",
        "quote_another": "💹 Autre cotation",

        # Compare
        "compare_prompt": (
            "📈 *Quelles actions comparer ?*\n\n"
            "Exemples :\n"
            "• `NVDA, AMD, INTC`\n"
            "• `AAPL MSFT GOOGL`\n\n"
            "💡 _Envoyez 2-5 tickers séparés par virgule ou espace_"
        ),
        "compare_error": "❌ Impossible de comparer",
        "compare_another": "📈 Autre comparaison",

        # Settings
        "settings": "⚙️ *Paramètres*",
        "change_language": "🌍 Changer de langue",

        # Navigation
        "back_menu": "🏠 Menu principal",
        "help": "❓ Aide",

        # Help
        "help_text": (
            "🤖 *Agent de Recherche Financière*\n\n"
            "Je suis un analyste financier IA capable de :\n\n"
            "📊 *Analyser* - Analyse approfondie avec SEC filings, news et données de marché\n"
            "💹 *Cotation* - Prix en temps réel et métriques clés\n"
            "📈 *Comparer* - Comparaison côte à côte de plusieurs actions\n\n"
            "💡 *Astuces :*\n"
            "• Vous pouvez aussi écrire naturellement - je comprends le contexte !\n"
            "• Essayez : \"Que se passe-t-il avec NVIDIA ?\"\n"
            "• Ou : \"Compare Apple et Microsoft\"\n\n"
            "🌍 Changez la langue dans Paramètres"
        ),

        # Natural language patterns
        "understood_analyze": "🔍 Compris ! Analyse en cours...",
        "understood_quote": "💹 Récupération de {ticker}...",
        "understood_compare": "📈 Comparaison de {tickers}...",
        "not_understood": (
            "🤔 Je ne suis pas sûr de comprendre.\n\n"
            "Utilisez les boutons du menu ou soyez plus précis !"
        ),
    },
}


def get_text(key: str, lang: Language = "en", **kwargs: str) -> str:
    """Get translated text.

    Args:
        key: Message key
        lang: Language code
        **kwargs: Format arguments

    Returns:
        Translated and formatted string
    """
    text = MESSAGES.get(lang, MESSAGES["en"]).get(key, MESSAGES["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text

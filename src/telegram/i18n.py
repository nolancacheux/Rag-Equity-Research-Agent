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
        "analyze_step_1": "📡 *Fetching market data...*",
        "analyze_step_2": "📡 *Fetching market data...* ✓\n📰 *Searching financial news...*",
        "analyze_step_3": "📡 *Fetching market data...* ✓\n📰 *Searching financial news...* ✓\n📄 *Analyzing SEC filings...*",
        "analyze_step_4": "📡 *Fetching market data...* ✓\n📰 *Searching financial news...* ✓\n📄 *Analyzing SEC filings...* ✓\n🤖 *Generating report...*",
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
            "*Core Features:*\n"
            "📊 *Analyze* - Deep analysis with SEC filings, news, market data\n"
            "💹 *Quote* - Real-time prices and key metrics\n"
            "📈 *Compare* - Side-by-side stock comparison\n\n"
            "*Advanced Tools:*\n"
            "💰 *DCF Valuation* - Calculate fair value\n"
            "⚠️ *Risk Score* - 10-K risk analysis (1-10)\n"
            "👥 *Peer Comparison* - Compare vs competitors\n"
            "🔴 *Reddit Sentiment* - WSB/stocks sentiment\n"
            "📅 *Earnings Calendar* - Upcoming earnings dates\n"
            "📜 *History* - Price history & earnings reactions\n\n"
            "*Watchlist:*\n"
            "📋 Track stocks with `/watchlist`\n"
            "🔔 Set alerts with `/alert NVDA above 150`\n\n"
            "💡 Type naturally or use commands!"
        ),
        # Tools menu
        "tools_menu": (
            "🛠️ *Advanced Tools*\n\n"
            "Choose a tool below or use commands:\n"
            "• `/dcf NVDA` - Fair value calculation\n"
            "• `/risk NVDA` - Risk score from 10-K\n"
            "• `/peers NVDA` - Peer comparison\n"
            "• `/reddit NVDA` - Reddit sentiment\n"
            "• `/calendar` - Earnings calendar\n"
            "• `/history NVDA` - Price history"
        ),
        "tools_menu_fr": (
            "🛠️ *Outils Avancés*\n\n"
            "Choisissez un outil ou utilisez les commandes :\n"
            "• `/dcf NVDA` - Calcul de fair value\n"
            "• `/risk NVDA` - Score de risque du 10-K\n"
            "• `/peers NVDA` - Comparaison avec peers\n"
            "• `/reddit NVDA` - Sentiment Reddit\n"
            "• `/calendar` - Calendrier earnings\n"
            "• `/history NVDA` - Historique des prix"
        ),
        # DCF
        "dcf_prompt": "💰 *DCF Valuation*\n\nEnter a ticker: `/dcf NVDA`",
        # Risk
        "risk_prompt": "⚠️ *Risk Score*\n\nEnter a ticker: `/risk NVDA`",
        # Peers
        "peers_prompt": "👥 *Peer Comparison*\n\nEnter a ticker: `/peers NVDA`",
        # Reddit
        "reddit_prompt": "🔴 *Reddit Sentiment*\n\nEnter a ticker: `/reddit NVDA`",
        # Calendar
        "calendar_prompt": "📅 *Earnings Calendar*\n\nShowing upcoming earnings for your watchlist and major stocks.",
        # History
        "history_prompt": "📜 *Historical Analysis*\n\nEnter: `/history NVDA` or `/history NVDA earnings`",
        # Watchlist
        "watchlist_empty": "📋 *Your Watchlist*\n\nEmpty! Add stocks with:\n`/watchlist add NVDA`",
        "watchlist_add_prompt": "➕ *Add to Watchlist*\n\nSend a ticker: `NVDA`",
        "watchlist_added": "✅ Added *{ticker}* to watchlist!",
        "watchlist_removed": "✅ Removed *{ticker}* from watchlist!",
        # Alerts
        "alerts_prompt": (
            "🔔 *Price Alerts*\n\n"
            "Set an alert:\n"
            "`/alert NVDA above 150`\n"
            "`/alert TSLA below 200`\n"
            "`/alert AAPL pe_above 30`"
        ),
        "alert_created": "🔔 Alert set: *{ticker}* {type} ${threshold}",
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
        "analyze_step_1": "📡 *Récupération des données de marché...*",
        "analyze_step_2": "📡 *Récupération des données de marché...* ✓\n📰 *Recherche des actualités...*",
        "analyze_step_3": "📡 *Récupération des données de marché...* ✓\n📰 *Recherche des actualités...* ✓\n📄 *Analyse des documents SEC...*",
        "analyze_step_4": "📡 *Récupération des données de marché...* ✓\n📰 *Recherche des actualités...* ✓\n📄 *Analyse des documents SEC...* ✓\n🤖 *Génération du rapport...*",
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
            "*Fonctions principales :*\n"
            "📊 *Analyser* - Analyse avec SEC filings, news, données marché\n"
            "💹 *Cotation* - Prix temps réel et métriques\n"
            "📈 *Comparer* - Comparaison côte à côte\n\n"
            "*Outils avancés :*\n"
            "💰 *Valorisation DCF* - Calcul fair value\n"
            "⚠️ *Score Risque* - Analyse 10-K (1-10)\n"
            "👥 *Peers* - Comparaison concurrents\n"
            "🔴 *Sentiment Reddit* - WSB/stocks\n"
            "📅 *Calendrier Earnings* - Prochains earnings\n"
            "📜 *Historique* - Prix et réactions earnings\n\n"
            "*Watchlist :*\n"
            "📋 Suivre avec `/watchlist`\n"
            "🔔 Alertes avec `/alert NVDA above 150`\n\n"
            "💡 Écrivez naturellement ou utilisez les commandes !"
        ),
        # Tools menu
        "tools_menu": (
            "🛠️ *Outils Avancés*\n\n"
            "Choisissez un outil ou commande :\n"
            "• `/dcf NVDA` - Calcul fair value\n"
            "• `/risk NVDA` - Score risque 10-K\n"
            "• `/peers NVDA` - Comparaison peers\n"
            "• `/reddit NVDA` - Sentiment Reddit\n"
            "• `/calendar` - Calendrier earnings\n"
            "• `/history NVDA` - Historique prix"
        ),
        # DCF
        "dcf_prompt": "💰 *Valorisation DCF*\n\nEntrez un ticker : `/dcf NVDA`",
        # Risk
        "risk_prompt": "⚠️ *Score Risque*\n\nEntrez un ticker : `/risk NVDA`",
        # Peers
        "peers_prompt": "👥 *Comparaison Peers*\n\nEntrez un ticker : `/peers NVDA`",
        # Reddit
        "reddit_prompt": "🔴 *Sentiment Reddit*\n\nEntrez un ticker : `/reddit NVDA`",
        # Calendar
        "calendar_prompt": "📅 *Calendrier Earnings*\n\nAffiche les prochains earnings de votre watchlist.",
        # History
        "history_prompt": "📜 *Analyse Historique*\n\nEntrez : `/history NVDA` ou `/history NVDA earnings`",
        # Watchlist
        "watchlist_empty": "📋 *Votre Watchlist*\n\nVide ! Ajoutez avec :\n`/watchlist add NVDA`",
        "watchlist_add_prompt": "➕ *Ajouter à la Watchlist*\n\nEnvoyez un ticker : `NVDA`",
        "watchlist_added": "✅ *{ticker}* ajouté à la watchlist !",
        "watchlist_removed": "✅ *{ticker}* retiré de la watchlist !",
        # Alerts
        "alerts_prompt": (
            "🔔 *Alertes Prix*\n\n"
            "Créer une alerte :\n"
            "`/alert NVDA above 150`\n"
            "`/alert TSLA below 200`\n"
            "`/alert AAPL pe_above 30`"
        ),
        "alert_created": "🔔 Alerte créée : *{ticker}* {type} ${threshold}",
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

# Telegram Bot Documentation

Complete guide to the Equity Research Agent Telegram bot.

## Setup

### 1. Create Bot with BotFather

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Choose a name (e.g., "Equity Research Agent")
4. Choose a username (e.g., "equity_research_bot")
5. Save the token

### 2. Configure Environment

```bash
# .env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
API_BASE_URL=http://localhost:8000  # Or your deployed API URL
```

### 3. Run the Bot

```bash
# With the API running
python -m src.telegram.bot

# Or with Docker
docker-compose up telegram-bot
```

## Commands

### Core Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `/start` | - | Welcome & language selection |
| `/menu` | - | Main menu with inline buttons |
| `/help` | - | Feature overview |
| `/analyze <query>` | `/a` | Deep research analysis |
| `/quote <ticker>` | `/q` | Real-time stock quote |
| `/compare <tickers>` | `/c` | Compare multiple stocks |

### Advanced Tools

| Command | Alias | Description |
|---------|-------|-------------|
| `/dcf <ticker>` | `/valuation` | DCF fair value calculation |
| `/risk <ticker>` | - | Risk score from 10-K (1-10) |
| `/peers <ticker>` | - | Peer comparison |
| `/reddit <ticker>` | `/wsb` | Reddit sentiment analysis |
| `/calendar` | `/earnings` | Earnings calendar |
| `/history <ticker>` | `/hist` | Price history |
| `/history <ticker> earnings` | - | Earnings reactions |

### Watchlist & Alerts

| Command | Alias | Description |
|---------|-------|-------------|
| `/watchlist` | `/wl` | View your watchlist |
| `/watchlist add <ticker>` | - | Add to watchlist |
| `/watchlist remove <ticker>` | - | Remove from watchlist |
| `/alert <ticker> above <price>` | - | Price alert (above) |
| `/alert <ticker> below <price>` | - | Price alert (below) |
| `/alert <ticker> pe_above <value>` | - | P/E alert |

## Inline Buttons

The bot uses inline keyboards for easy navigation:

### Main Menu
```
┌─────────────┬─────────────┐
│ 📊 Analyze  │ 💹 Quote    │
├─────────────┼─────────────┤
│ 📈 Compare  │ 🛠️ Tools    │
├─────────────┼─────────────┤
│ 📋 Watchlist│ ⚙️ Settings │
└─────────────┴─────────────┘
```

### Tools Menu
```
┌─────────────────┬─────────────────┐
│ 💰 DCF Valuation│ ⚠️ Risk Score   │
├─────────────────┼─────────────────┤
│ 👥 Peer Compare │ 🔴 Reddit       │
├─────────────────┼─────────────────┤
│ 📅 Earnings Cal │ 📜 History      │
├─────────────────┴─────────────────┤
│           ◀️ Back                 │
└───────────────────────────────────┘
```

### Watchlist Menu
```
┌─────────────────┬─────────────────┐
│ ➕ Add Stock    │ 🔔 My Alerts    │
├─────────────────┴─────────────────┤
│      📅 Watchlist Earnings        │
├───────────────────────────────────┤
│           ◀️ Back                 │
└───────────────────────────────────┘
```

## Natural Language

The bot understands natural language queries:

```
"What's happening with NVIDIA?"
→ Triggers analysis

"NVDA"
→ Returns quote

"Compare Apple and Microsoft"
→ Triggers comparison

"Analyze TSLA China risks"
→ Deep analysis with SEC filing search
```

## Languages

Supported languages:
- 🇬🇧 English (default)
- 🇫🇷 Français

Change in Settings menu or with `/start`.

## Examples

### Quick Quote
```
You: NVDA
Bot: 💹 NVIDIA Corporation (NVDA)
     Price: $142.50 (+2.3%)
     Market Cap: $3.5T
     P/E Ratio: 65.2
     Volume: 45.2M
```

### Deep Analysis
```
You: /analyze What are the risks for NVIDIA related to China?

Bot: 📡 Fetching market data... ✓
     📰 Searching news... ✓
     📄 Analyzing SEC filings... ✓
     🤖 Generating report...

     # Equity Research: NVIDIA
     ## Executive Summary
     ...
```

### DCF Valuation
```
You: /dcf AAPL

Bot: 💰 DCF Valuation: AAPL
     
     Current Price: $185.50
     Fair Value: $165.20
     Upside: -10.9% 🔴 OVERVALUED
     
     ### Assumptions
     - FCF (TTM): $99.58B
     - Growth Rate: 5.2%
     - Discount Rate: 10.0%
     - Terminal Growth: 2.5%
```

### Reddit Sentiment
```
You: /reddit GME

Bot: 🔴 Reddit Sentiment: GME
     
     Overall: Bullish (+0.45) 🟢
     Mentions: 234 posts
     Bullish/Bearish: 156/78
     
     ### Trending Topics
     DRS, squeeze, earnings, moon
     
     ### Top Discussions
     - [WSB] GME to the moon! 🚀 (bullish)
     - [stocks] GME earnings preview (neutral)
```

## File Structure

```
src/telegram/
├── bot.py           # Application entry point
├── handlers.py      # Core command handlers
├── handlers_v2.py   # New feature handlers
├── keyboards.py     # Inline keyboard layouts
├── i18n.py          # Translations (EN/FR)
├── client.py        # API client
├── formatters.py    # Message formatting
└── storage.py       # User state storage
```

## Customization

### Adding Commands

1. Create handler in `handlers.py` or `handlers_v2.py`:
```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello!")
```

2. Register in `bot.py`:
```python
application.add_handler(CommandHandler("mycommand", my_command))
```

### Adding Keyboards

Edit `keyboards.py`:
```python
def my_keyboard(lang: Language = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Button", callback_data="my:action")],
    ])
```

### Adding Translations

Edit `i18n.py`:
```python
MESSAGES = {
    "en": {
        "my_key": "English text",
    },
    "fr": {
        "my_key": "Texte français",
    },
}
```

## Deployment

### Docker

```dockerfile
# Included in docker-compose.yml
services:
  telegram-bot:
    build:
      context: .
      dockerfile: Dockerfile.telegram
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - API_BASE_URL=http://api:8000
```

### Azure Container Apps

See [Azure Deployment Guide](azure-deployment.md).

## Troubleshooting

### Bot not responding

1. Check token is correct
2. Verify API is running and accessible
3. Check logs: `docker logs equity-telegram-bot`

### API errors

1. Ensure API_BASE_URL is set correctly
2. Check API health: `curl $API_BASE_URL/health`
3. Verify API key if authentication is enabled

### Rate limiting

- The bot respects Telegram rate limits
- API has built-in rate limiting (see API docs)

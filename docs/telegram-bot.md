# Telegram Bot

The Equity Research Agent includes a Telegram bot interface for quick stock analysis on the go.

## Features

- **Multi-language**: English and French (auto-detected or user choice)
- **Real-time progress**: Shows analysis steps as they happen
- **Inline keyboards**: Easy navigation without typing commands
- **Smart parsing**: Understands natural language queries

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram      │────▶│  Telegram Bot   │────▶│   FastAPI       │
│   (User)        │◀────│  (Container)    │◀────│   (Container)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                              │  X-API-Key header      │
                              │                        ▼
                              │                 ┌─────────────────┐
                              │                 │  Qdrant + Redis │
                              │                 └─────────────────┘
                              ▼                        │
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Azure OpenAI   │     │  yfinance/SEC   │
                        └─────────────────┘     └─────────────────┘
```

## Commands

| Command | Alias | Description | Example |
|---------|-------|-------------|---------|
| `/start` | - | Welcome + language selection | `/start` |
| `/help` | - | Show all commands | `/help` |
| `/quote <TICKER>` | `/q` | Get stock quote | `/quote NVDA` |
| `/compare <T1,T2,...>` | `/c` | Compare stocks | `/compare NVDA,AMD,INTC` |
| `/analyze <query>` | `/a` | Full AI analysis | `/analyze Compare NVIDIA vs AMD` |

## Natural Language

The bot understands context. No need for commands:

- "What's happening with NVIDIA?" → triggers analysis
- "NVDA" → shows quote
- "Compare Apple and Microsoft" → runs comparison

## Progress Steps

During analysis, the bot shows real-time progress:

```
📡 Fetching market data... ✓
📰 Searching financial news... ✓
📄 Analyzing SEC filings...
🤖 Generating report...
```

## Local Development

### Prerequisites

- Bot token from [@BotFather](https://t.me/BotFather)
- Running API (via docker-compose or uvicorn)

### Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram

2. Add configuration to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token_here
   API_BASE_URL=http://localhost:8000
   API_SECRET_KEY=your-api-key  # Must match API's key
   ```

3. Start all services:
   ```bash
   docker compose up -d
   ```

4. Or run bot separately:
   ```bash
   # Terminal 1: Start API + infra
   docker compose up -d qdrant redis
   uvicorn src.api.main:app --reload
   
   # Terminal 2: Start bot
   python run_telegram_bot.py
   ```

## API Authentication

The bot automatically includes `X-API-Key` header when `API_SECRET_KEY` is configured.

Both the API and bot must have the **same** `API_SECRET_KEY`:

```bash
# Generate a key
openssl rand -hex 32

# Add to both .env files (or Azure secrets)
API_SECRET_KEY=1e6cbdd9414027a8c9d0ef3c98296d85...
```

## Azure Deployment

The bot runs as a separate Container App alongside the API.

### Infrastructure

- **Container**: `equity-research-telegram-bot`
- **Resources**: 0.25 CPU, 0.5Gi memory
- **Replicas**: Always 1 (to avoid duplicate messages)
- **Ingress**: None (uses outbound polling)

### Required Azure Secrets

| Secret | Description |
|--------|-------------|
| `telegram-bot-token` | Bot API token from BotFather |
| `api-secret-key` | API authentication key |
| `azure-openai-key` | Azure OpenAI API key |

### Deploy

```bash
# Add secrets to Azure
az containerapp secret set --name equity-research-telegram-bot \
  --resource-group equity-research-rg \
  --secrets telegram-bot-token="YOUR_TOKEN" api-secret-key="YOUR_KEY"

# Update env vars
az containerapp update --name equity-research-telegram-bot \
  --resource-group equity-research-rg \
  --set-env-vars "API_SECRET_KEY=secretref:api-secret-key"
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot API token | Yes |
| `API_BASE_URL` | FastAPI URL | Yes |
| `API_SECRET_KEY` | API auth key | Yes (prod) |
| `APP_ENV` | Environment (dev/prod) | No |

## Internationalization (i18n)

The bot supports English and French:

```
src/telegram/i18n.py
├── MESSAGES["en"]  # English translations
└── MESSAGES["fr"]  # French translations
```

Users select language on first `/start`, stored in user preferences.

## Code Structure

```
src/telegram/
├── bot.py          # Bot initialization
├── handlers.py     # Command and callback handlers
├── client.py       # HTTP client for API calls
├── formatters.py   # Format API responses for Telegram
├── keyboards.py    # Inline keyboard builders
├── i18n.py         # Translations
└── storage.py      # User preferences (file-based)
```

## Security Considerations

1. **Token Security**: Never commit bot tokens. Use Azure Key Vault in production.
2. **API Auth**: Always use `API_SECRET_KEY` in production.
3. **Rate Limiting**: The bot inherits API rate limits (10 req/min for analysis).
4. **Access Control**: Consider adding user whitelist for private bots.

## Adding User Whitelist (Optional)

To restrict bot access to specific users:

```python
# In src/telegram/handlers.py

ALLOWED_USERS = {123456789, 987654321}  # Telegram user IDs

async def check_authorized(update: Update) -> bool:
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Unauthorized.")
        return False
    return True
```

## Troubleshooting

### Bot not responding

1. Check if bot is running:
   ```bash
   docker compose logs telegram-bot
   ```

2. Verify token is correct:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getMe
   ```

3. Check for import errors in logs.

### API 401 Unauthorized

Ensure `API_SECRET_KEY` matches between bot and API:
```bash
# Check API accepts the key
curl -H "X-API-Key: your-key" https://your-api/health
```

### Connection errors to API

1. Check API health:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify `API_BASE_URL` is correct and reachable from bot container.

### Duplicate messages

Ensure only ONE bot instance is running. In Azure, `max_replicas = 1` prevents this.

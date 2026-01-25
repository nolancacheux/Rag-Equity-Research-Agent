# Telegram Bot

The Equity Research Agent includes a Telegram bot interface for quick stock analysis on the go.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram      │────▶│  Telegram Bot   │────▶│   FastAPI       │
│   (User)        │◀────│  (Container)    │◀────│   (Container)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                              │                        ▼
                              │                 ┌─────────────────┐
                              │                 │  Qdrant + Redis │
                              │                 └─────────────────┘
                              │                        │
                              ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Azure OpenAI   │     │  yfinance/SEC   │
                        └─────────────────┘     └─────────────────┘
```

## Commands

| Command | Alias | Description | Example |
|---------|-------|-------------|---------|
| `/start` | - | Welcome message | `/start` |
| `/help` | - | Show all commands | `/help` |
| `/quote <TICKER>` | `/q` | Get stock quote | `/quote NVDA` |
| `/compare <T1,T2,...>` | `/c` | Compare stocks | `/compare NVDA,AMD,INTC` |
| `/analyze <query>` | `/a` | Full AI analysis | `/analyze Compare NVIDIA vs AMD` |

## Local Development

### Prerequisites

- Bot token from [@BotFather](https://t.me/BotFather)
- Running API (via docker-compose or uvicorn)

### Setup

1. Add token to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

2. Start all services:
   ```bash
   docker compose up -d
   ```

3. Or run bot separately:
   ```bash
   # Terminal 1: Start API
   docker compose up -d qdrant redis
   uvicorn src.api.main:app --reload
   
   # Terminal 2: Start bot
   python run_telegram_bot.py
   ```

## Azure Deployment

The bot runs as a separate Container App alongside the API.

### Infrastructure

- **Container**: `equity-research-telegram-bot`
- **Resources**: 0.25 CPU, 0.5Gi memory
- **Replicas**: Always 1 (to avoid duplicate messages)
- **Ingress**: None (uses outbound polling)

### Deploy

```bash
# Full deployment
./scripts/deploy.sh full

# Or step by step
./scripts/deploy.sh init    # Initialize Terraform
./scripts/deploy.sh plan    # Review changes
./scripts/deploy.sh apply   # Create infrastructure
./scripts/deploy.sh build   # Build & push images
./scripts/deploy.sh update  # Update containers
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot API token | Yes |
| `API_BASE_URL` | FastAPI URL | Yes |
| `AZURE_OPENAI_*` | Azure OpenAI credentials | Yes |
| `APP_ENV` | Environment (dev/prod) | No |

## Security Considerations

1. **Token Security**: Never commit bot tokens. Use Azure Key Vault in production.
2. **Rate Limiting**: The bot inherits API rate limits (10 req/min for analysis).
3. **Access Control**: Consider adding user whitelist for private bots.

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

### Connection errors to API

1. Check API health:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify `API_BASE_URL` is correct in bot environment.

### Duplicate messages

Ensure only ONE bot instance is running. In Azure, `max_replicas = 1` prevents this.

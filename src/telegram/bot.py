"""Main Telegram bot entry point."""

import logging
import os
import sys

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.telegram.client import APIClient
from src.telegram.handlers import (
    analyze_command,
    callback_handler,
    compare_command,
    help_command,
    menu_command,
    message_handler,
    quote_command,
    set_api_client,
    start_command,
)
from telegram import Update

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "❌ An error occurred. Please try again or use /start to restart."
        )


def create_application(token: str, api_base_url: str | None = None) -> Application:  # type: ignore[type-arg]
    """Create and configure the Telegram bot application.

    Args:
        token: Telegram bot token.
        api_base_url: Optional API base URL override.

    Returns:
        Configured Application instance.
    """
    # Initialize API client
    client = APIClient(base_url=api_base_url)
    set_api_client(client)

    # Build application
    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("q", quote_command))
    application.add_handler(CommandHandler("compare", compare_command))
    application.add_handler(CommandHandler("c", compare_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("a", analyze_command))

    # Callback query handler (for inline buttons)
    application.add_handler(CallbackQueryHandler(callback_handler))

    # Message handler (for free text)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    # Error handler
    application.add_error_handler(error_handler)

    return application


def run_bot(
    token: str | None = None,
    api_base_url: str | None = None,
) -> None:
    """Run the Telegram bot.

    Args:
        token: Telegram bot token. If not provided, uses TELEGRAM_BOT_TOKEN env var.
        api_base_url: Optional API base URL override.
    """
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    # Get API URL from env if not provided
    if not api_base_url:
        api_base_url = os.environ.get(
            "API_BASE_URL",
            "https://equity-research-agent.thankfulhill-01e4fbbb.swedencentral.azurecontainerapps.io",
        )

    logger.info(f"Starting bot with API URL: {api_base_url}")

    app = create_application(token, api_base_url)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


def main() -> None:
    """Main entry point."""
    run_bot()


if __name__ == "__main__":
    main()

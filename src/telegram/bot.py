"""Main Telegram bot entry point."""

import asyncio
import logging
import os
import sys

from telegram.ext import Application, CommandHandler, ContextTypes

from src.telegram.client import APIClient
from src.telegram.handlers import (
    analyze_command,
    compare_command,
    help_command,
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
    """Handle errors in the bot.

    Args:
        update: Update that caused the error.
        context: Callback context with error info.
    """
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "An error occurred while processing your request. Please try again later."
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

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("q", quote_command))  # Alias
    application.add_handler(CommandHandler("compare", compare_command))
    application.add_handler(CommandHandler("c", compare_command))  # Alias
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("a", analyze_command))  # Alias

    # Add error handler
    application.add_error_handler(error_handler)

    return application


def run_bot(
    token: str | None = None,
    api_base_url: str | None = None,
) -> None:
    """Run the Telegram bot.

    Args:
        token: Telegram bot token. If not provided, reads from TELEGRAM_BOT_TOKEN env var.
        api_base_url: API base URL. If not provided, reads from API_BASE_URL or defaults to localhost.
    """
    # Get token
    bot_token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    # Get API URL
    api_url = api_base_url or os.getenv("API_BASE_URL", "http://localhost:8000")

    logger.info(f"Starting bot with API URL: {api_url}")

    # Create and run application
    application = create_application(bot_token, api_url)

    # Run with polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def run_bot_async(
    token: str | None = None,
    api_base_url: str | None = None,
) -> None:
    """Run the Telegram bot asynchronously.

    Args:
        token: Telegram bot token.
        api_base_url: API base URL.
    """
    bot_token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    api_url = api_base_url or os.getenv("API_BASE_URL", "http://localhost:8000")

    logger.info(f"Starting bot (async) with API URL: {api_url}")

    application = create_application(bot_token, api_url)

    # Initialize and start
    await application.initialize()
    await application.start()
    await application.updater.start_polling()  # type: ignore[union-attr]

    # Keep running until stopped
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await application.updater.stop()  # type: ignore[union-attr]
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    run_bot()

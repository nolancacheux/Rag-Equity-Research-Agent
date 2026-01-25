#!/usr/bin/env python3
"""Entry point to run the Telegram bot."""

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.telegram.bot import run_bot

if __name__ == "__main__":
    run_bot()

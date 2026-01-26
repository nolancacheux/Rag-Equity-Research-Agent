"""Simple chat service for conversational responses."""

import structlog
from langchain_groq import ChatGroq

from src.config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

# System prompt for short, helpful responses
SYSTEM_PROMPT = """You are FinanceAgent, a helpful financial assistant bot.
Keep responses SHORT (1-2 sentences max).
Be friendly and professional.
If asked about stocks, suggest using commands like /q TICKER for quotes or /analyze for analysis.
Available commands: /q, /analyze, /compare, /dcf, /risk, /peers, /watchlist, /help
Respond in the same language as the user (English or French)."""


class ChatService:
    """Simple chat service using Groq."""

    def __init__(self) -> None:
        """Initialize chat service."""
        self._llm = None
        if settings.groq_api_key:
            self._llm = ChatGroq(
                api_key=settings.groq_api_key,
                model="llama-3.1-8b-instant",  # Fast and cheap
                temperature=0.7,
                max_tokens=100,  # Keep responses short
            )

    async def chat(self, message: str) -> str:
        """Generate a short conversational response.

        Args:
            message: User message

        Returns:
            Short response string
        """
        if not self._llm:
            return "Hello! I'm FinanceAgent. Use /help to see available commands."

        try:
            response = await self._llm.ainvoke(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ]
            )
            return response.content.strip()
        except Exception as e:
            logger.error("chat_failed", error=str(e))
            return "Hello! How can I help? Use /help for commands."


# Singleton instance
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Get or create chat service singleton."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service

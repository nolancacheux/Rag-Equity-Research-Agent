"""User preferences storage for Telegram bot."""

import json
import logging
from pathlib import Path
from typing import Any

from src.telegram.i18n import Language

logger = logging.getLogger(__name__)

# Simple file-based storage (no Redis dependency for bot)
# Using /tmp is intentional for ephemeral container storage
STORAGE_FILE = Path("/tmp/telegram_bot_users.json")  # nosec B108


class UserPreferences:
    """Manages user preferences."""

    def __init__(self) -> None:
        """Initialize storage."""
        self._cache: dict[int, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load preferences from file."""
        try:
            if STORAGE_FILE.exists():
                with open(STORAGE_FILE) as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    self._cache = {int(k): v for k, v in data.items()}
                logger.info(f"Loaded {len(self._cache)} user preferences")
        except Exception as e:
            logger.warning(f"Could not load preferences: {e}")
            self._cache = {}

    def _save(self) -> None:
        """Save preferences to file."""
        try:
            with open(STORAGE_FILE, "w") as f:
                json.dump(self._cache, f)
        except Exception as e:
            logger.warning(f"Could not save preferences: {e}")

    def get_language(self, user_id: int) -> Language | None:
        """Get user's preferred language.

        Args:
            user_id: Telegram user ID

        Returns:
            Language code or None if not set
        """
        user_data = self._cache.get(user_id, {})
        lang = user_data.get("language")
        if lang in ("en", "fr"):
            return lang  # type: ignore
        return None

    def set_language(self, user_id: int, language: Language) -> None:
        """Set user's preferred language.

        Args:
            user_id: Telegram user ID
            language: Language code
        """
        if user_id not in self._cache:
            self._cache[user_id] = {}
        self._cache[user_id]["language"] = language
        self._save()
        logger.info(f"User {user_id} set language to {language}")

    def get_state(self, user_id: int) -> str | None:
        """Get user's conversation state.

        Args:
            user_id: Telegram user ID

        Returns:
            State string or None
        """
        return self._cache.get(user_id, {}).get("state")

    def set_state(self, user_id: int, state: str | None) -> None:
        """Set user's conversation state.

        Args:
            user_id: Telegram user ID
            state: State string or None to clear
        """
        if user_id not in self._cache:
            self._cache[user_id] = {}
        if state is None:
            self._cache[user_id].pop("state", None)
        else:
            self._cache[user_id]["state"] = state
        self._save()

    def is_new_user(self, user_id: int) -> bool:
        """Check if this is a new user.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user has no preferences set
        """
        return user_id not in self._cache or "language" not in self._cache.get(user_id, {})


# Singleton instance
_storage: UserPreferences | None = None


def get_storage() -> UserPreferences:
    """Get storage singleton."""
    global _storage
    if _storage is None:
        _storage = UserPreferences()
    return _storage

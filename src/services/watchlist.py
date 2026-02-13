"""Watchlist and price alerts service."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import structlog

logger = structlog.get_logger()


class AlertType(StrEnum):
    """Type of price alert."""

    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PERCENT_CHANGE = "percent_change"
    PE_ABOVE = "pe_above"
    PE_BELOW = "pe_below"
    VOLUME_SPIKE = "volume_spike"


@dataclass
class Alert:
    """Price alert configuration."""

    id: str
    ticker: str
    alert_type: AlertType
    threshold: float
    created_at: str
    triggered: bool = False
    triggered_at: str | None = None
    message: str | None = None


@dataclass
class WatchlistItem:
    """Watchlist item with metadata."""

    ticker: str
    added_at: str
    notes: str | None = None
    alerts: list[Alert] | None = None
    last_price: float | None = None
    last_updated: str | None = None


class WatchlistService:
    """Manage user watchlists and price alerts.

    Stores data in a JSON file for simplicity (no database needed).
    """

    def __init__(self, storage_path: str | None = None) -> None:
        """Initialize watchlist service.

        Args:
            storage_path: Path to storage file. Defaults to /tmp/watchlist.json.
        """
        self.storage_path = Path(storage_path or "/tmp/watchlist.json")  # nosec B108
        self._data: dict = {"watchlists": {}, "alerts": []}
        self._load()

    def _load(self) -> None:
        """Load data from storage."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path) as f:
                    self._data = json.load(f)
        except Exception as e:
            logger.warning("watchlist_load_failed", error=str(e))
            self._data = {"watchlists": {}, "alerts": []}

    def _save(self) -> None:
        """Save data to storage."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            logger.warning("watchlist_save_failed", error=str(e))

    # Watchlist operations
    def add_to_watchlist(
        self, user_id: str, ticker: str, notes: str | None = None
    ) -> WatchlistItem:
        """Add a ticker to user's watchlist.

        Args:
            user_id: User identifier.
            ticker: Stock ticker symbol.
            notes: Optional notes about the stock.

        Returns:
            Created WatchlistItem.
        """
        ticker = ticker.upper()

        if user_id not in self._data["watchlists"]:
            self._data["watchlists"][user_id] = {}

        item = WatchlistItem(
            ticker=ticker,
            added_at=datetime.now().isoformat(),
            notes=notes,
            alerts=[],
        )

        self._data["watchlists"][user_id][ticker] = asdict(item)
        self._save()

        logger.info("watchlist_add", user_id=user_id, ticker=ticker)
        return item

    def remove_from_watchlist(self, user_id: str, ticker: str) -> bool:
        """Remove a ticker from user's watchlist.

        Args:
            user_id: User identifier.
            ticker: Stock ticker symbol.

        Returns:
            True if removed, False if not found.
        """
        ticker = ticker.upper()

        if user_id in self._data["watchlists"]:
            if ticker in self._data["watchlists"][user_id]:
                del self._data["watchlists"][user_id][ticker]
                self._save()
                logger.info("watchlist_remove", user_id=user_id, ticker=ticker)
                return True
        return False

    def get_watchlist(self, user_id: str) -> list[WatchlistItem]:
        """Get user's watchlist.

        Args:
            user_id: User identifier.

        Returns:
            List of WatchlistItem objects.
        """
        items = []
        if user_id in self._data["watchlists"]:
            for _ticker, data in self._data["watchlists"][user_id].items():
                items.append(WatchlistItem(**data))
        return items

    # Alert operations
    def create_alert(
        self,
        user_id: str,
        ticker: str,
        alert_type: AlertType,
        threshold: float,
        message: str | None = None,
    ) -> Alert:
        """Create a price alert.

        Args:
            user_id: User identifier.
            ticker: Stock ticker symbol.
            alert_type: Type of alert.
            threshold: Threshold value.
            message: Custom message when triggered.

        Returns:
            Created Alert object.
        """
        ticker = ticker.upper()
        alert_id = f"{user_id}_{ticker}_{alert_type.value}_{threshold}"

        alert = Alert(
            id=alert_id,
            ticker=ticker,
            alert_type=alert_type,
            threshold=threshold,
            created_at=datetime.now().isoformat(),
            message=message,
        )

        # Store alert
        alert_data = asdict(alert)
        alert_data["user_id"] = user_id
        self._data["alerts"].append(alert_data)
        self._save()

        logger.info(
            "alert_created",
            user_id=user_id,
            ticker=ticker,
            alert_type=alert_type.value,
            threshold=threshold,
        )
        return alert

    def get_user_alerts(self, user_id: str) -> list[Alert]:
        """Get all alerts for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of Alert objects.
        """
        alerts = []
        for alert_data in self._data["alerts"]:
            if alert_data.get("user_id") == user_id:
                # Remove user_id for Alert construction
                data = {k: v for k, v in alert_data.items() if k != "user_id"}
                data["alert_type"] = AlertType(data["alert_type"])
                alerts.append(Alert(**data))
        return alerts

    def delete_alert(self, user_id: str, alert_id: str) -> bool:
        """Delete an alert.

        Args:
            user_id: User identifier.
            alert_id: Alert identifier.

        Returns:
            True if deleted, False if not found.
        """
        for i, alert_data in enumerate(self._data["alerts"]):
            if alert_data.get("id") == alert_id and alert_data.get("user_id") == user_id:
                del self._data["alerts"][i]
                self._save()
                logger.info("alert_deleted", user_id=user_id, alert_id=alert_id)
                return True
        return False

    def check_alerts(
        self,
        ticker: str,
        current_price: float,
        pe_ratio: float | None = None,
        volume: int | None = None,
    ) -> list[tuple[str, Alert]]:
        """Check if any alerts are triggered for a ticker.

        Args:
            ticker: Stock ticker symbol.
            current_price: Current stock price.
            pe_ratio: Current P/E ratio (optional).
            volume: Current volume (optional).

        Returns:
            List of (user_id, Alert) tuples for triggered alerts.
        """
        ticker = ticker.upper()
        triggered = []

        for alert_data in self._data["alerts"]:
            if alert_data["ticker"] != ticker or alert_data["triggered"]:
                continue

            user_id = alert_data["user_id"]
            alert_type = AlertType(alert_data["alert_type"])
            threshold = alert_data["threshold"]

            is_triggered = False

            if alert_type == AlertType.PRICE_ABOVE and current_price >= threshold:
                is_triggered = True
            elif alert_type == AlertType.PRICE_BELOW and current_price <= threshold:
                is_triggered = True
            elif alert_type == AlertType.PE_ABOVE and pe_ratio and pe_ratio >= threshold:
                is_triggered = True
            elif alert_type == AlertType.PE_BELOW and pe_ratio and pe_ratio <= threshold:
                is_triggered = True

            if is_triggered:
                # Mark as triggered
                alert_data["triggered"] = True
                alert_data["triggered_at"] = datetime.now().isoformat()

                data = {k: v for k, v in alert_data.items() if k != "user_id"}
                data["alert_type"] = AlertType(data["alert_type"])
                triggered.append((user_id, Alert(**data)))

        if triggered:
            self._save()

        return triggered


# Singleton instance
_watchlist_service: WatchlistService | None = None


def get_watchlist_service() -> WatchlistService:
    """Get singleton watchlist service instance."""
    global _watchlist_service
    if _watchlist_service is None:
        _watchlist_service = WatchlistService()
    return _watchlist_service

"""Dead Drop Pipeline — Telegram channel publisher.

Publishes content to a Telegram channel via Bot API.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramPublisher:
    """Publisher for Telegram channels."""

    def __init__(self) -> None:
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.channel_id = settings.TELEGRAM_CHANNEL_ID
        self.log = logger.bind(publisher="telegram")

        if not self.bot_token or not self.channel_id:
            self.log.warning("telegram.not_configured")

    def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_preview: bool = False,
    ) -> dict[str, Any] | None:
        """Send a text message to the Telegram channel.

        Args:
            text: Message text (max 4096 chars).
            parse_mode: 'HTML' or 'Markdown'.
            disable_preview: If True, don't show link previews.

        Returns:
            Telegram API response or None on error.
        """
        if not self.bot_token:
            self.log.error("telegram.no_bot_token")
            return None

        try:
            response = httpx.post(
                f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.channel_id,
                    "text": text[:4096],
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": disable_preview,
                },
                timeout=15.0,
            )
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                msg_id = result.get("result", {}).get("message_id")
                self.log.info(
                    "telegram.message_sent",
                    message_id=msg_id,
                    length=len(text),
                )
                return result
            else:
                self.log.error(
                    "telegram.api_not_ok",
                    description=result.get("description"),
                )
                return None

        except Exception as exc:
            self.log.exception("telegram.error", error=str(exc))
            return None

    def send_notification(self, text: str) -> dict[str, Any] | None:
        """Send a simple notification (deploy alerts, errors, etc.)."""
        return self.send_message(text, disable_preview=True)

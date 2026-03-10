"""Dead Drop Pipeline — beehiiv newsletter publisher.

Publishes newsletter content via the beehiiv API.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

BEEHIIV_API_BASE = "https://api.beehiiv.com/v2"


class BeehiivPublisher:
    """Publisher for beehiiv newsletters."""

    def __init__(self) -> None:
        self.api_key = settings.BEEHIIV_API_KEY
        self.publication_id = settings.BEEHIIV_PUBLICATION_ID
        self.log = logger.bind(publisher="beehiiv")

        if not self.api_key or not self.publication_id:
            self.log.warning("beehiiv.not_configured")

        self.client = httpx.Client(
            base_url=BEEHIIV_API_BASE,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def create_post(
        self,
        title: str,
        content_html: str,
        subtitle: str = "",
        status: str = "draft",
    ) -> dict[str, Any] | None:
        """Create a new newsletter post on beehiiv.

        Args:
            title: Post title.
            content_html: HTML content body.
            subtitle: Post subtitle/preview text.
            status: 'draft' or 'confirmed' (scheduled). Default draft for review.

        Returns:
            beehiiv API response dict, or None on error.
        """
        if not self.api_key:
            self.log.error("beehiiv.no_api_key")
            return None

        try:
            payload = {
                "publication_id": self.publication_id,
                "title": title,
                "subtitle": subtitle or title[:100],
                "content_html": content_html,
                "status": status,
            }

            response = self.client.post(
                f"/publications/{self.publication_id}/posts",
                json=payload,
            )
            response.raise_for_status()

            result = response.json()
            post_id = result.get("data", {}).get("id", "unknown")

            self.log.info(
                "beehiiv.post_created",
                post_id=post_id,
                title=title[:80],
                status=status,
            )

            return result

        except httpx.HTTPStatusError as exc:
            self.log.error(
                "beehiiv.api_error",
                status_code=exc.response.status_code,
                detail=exc.response.text[:200],
            )
            return None
        except Exception as exc:
            self.log.exception("beehiiv.error", error=str(exc))
            return None

    def list_posts(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent newsletter posts."""
        try:
            response = self.client.get(
                f"/publications/{self.publication_id}/posts",
                params={"limit": limit, "status": "confirmed"},
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as exc:
            self.log.exception("beehiiv.list_error", error=str(exc))
            return []

    def get_subscribers_count(self) -> int | None:
        """Get total active subscriber count."""
        try:
            response = self.client.get(
                f"/publications/{self.publication_id}/subscriptions",
                params={"limit": 1, "status": "active"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("total_results", 0)
        except Exception as exc:
            self.log.exception("beehiiv.subscribers_error", error=str(exc))
            return None

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

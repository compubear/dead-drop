"""Dead Drop Pipeline — Reddit publisher.

Posts content to Reddit via the Reddit API (PRAW-style).
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_BASE = "https://oauth.reddit.com"


class RedditPublisher:
    """Publisher for Reddit posts."""

    def __init__(self) -> None:
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET
        self.username = settings.REDDIT_USERNAME
        self.password = settings.REDDIT_PASSWORD
        self.log = logger.bind(publisher="reddit")
        self._access_token: str | None = None

        if not all([self.client_id, self.client_secret, self.username, self.password]):
            self.log.warning("reddit.not_configured")

    def _authenticate(self) -> bool:
        """Authenticate with Reddit API using password grant."""
        try:
            response = httpx.post(
                REDDIT_AUTH_URL,
                auth=(self.client_id, self.client_secret),
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                },
                headers={"User-Agent": "DeadDropBot/1.0 by DeadDropIntel"},
                timeout=15.0,
            )
            response.raise_for_status()

            data = response.json()
            self._access_token = data.get("access_token")

            if self._access_token:
                self.log.info("reddit.authenticated")
                return True

            self.log.error("reddit.auth_no_token")
            return False

        except Exception as exc:
            self.log.exception("reddit.auth_error", error=str(exc))
            return False

    def _get_headers(self) -> dict[str, str]:
        """Get authenticated request headers."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": "DeadDropBot/1.0 by DeadDropIntel",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def submit_post(
        self,
        subreddit: str,
        title: str,
        text: str,
    ) -> dict[str, Any] | None:
        """Submit a text post to a subreddit.

        Args:
            subreddit: Subreddit name (without r/).
            title: Post title.
            text: Post body (markdown).

        Returns:
            Reddit API response or None on error.
        """
        if not self._access_token:
            if not self._authenticate():
                return None

        try:
            response = httpx.post(
                f"{REDDIT_API_BASE}/api/submit",
                headers=self._get_headers(),
                data={
                    "sr": subreddit,
                    "kind": "self",
                    "title": title,
                    "text": text,
                    "sendreplies": "true",
                },
                timeout=15.0,
            )
            response.raise_for_status()

            result = response.json()
            success = result.get("success", False)

            if success:
                post_url = result.get("jquery", [[]])[0]
                self.log.info(
                    "reddit.post_submitted",
                    subreddit=subreddit,
                    title=title[:80],
                )
            else:
                errors = result.get("json", {}).get("errors", [])
                self.log.error(
                    "reddit.submit_failed",
                    errors=errors,
                )

            return result

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                self.log.warning("reddit.token_expired, re-authenticating")
                self._access_token = None
                return self.submit_post(subreddit, title, text)
            self.log.error(
                "reddit.api_error",
                status_code=exc.response.status_code,
            )
            return None
        except Exception as exc:
            self.log.exception("reddit.error", error=str(exc))
            return None

    def post_to_default_subs(
        self, title: str, text: str
    ) -> dict[str, dict[str, Any] | None]:
        """Post to Dead Drop's target subreddits.

        Returns:
            Dict mapping subreddit to API response.
        """
        target_subs = [
            "geopolitics",
            "IntelligenceHistory",
            "OSINT",
            "cybersecurity",
        ]

        results = {}
        for sub in target_subs:
            results[sub] = self.submit_post(sub, title, text)

        return results

"""Dead Drop Pipeline — Twitter/X publisher.

Publishes Twitter threads via the Twitter API v2.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

TWITTER_API_BASE = "https://api.twitter.com/2"


class TwitterPublisher:
    """Publisher for Twitter/X threads."""

    def __init__(self) -> None:
        self.bearer_token = settings.TWITTER_BEARER_TOKEN
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET
        self.access_token = settings.TWITTER_ACCESS_TOKEN
        self.access_secret = settings.TWITTER_ACCESS_SECRET
        self.log = logger.bind(publisher="twitter")

        if not self.bearer_token:
            self.log.warning("twitter.not_configured")

    def _get_oauth_headers(self) -> dict[str, str]:
        """Build OAuth 1.0a headers for user-context requests.

        Note: For production, use a proper OAuth library (tweepy, etc.)
        This is a placeholder that uses Bearer token for app-level access.
        """
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

    def post_tweet(self, text: str, reply_to: str | None = None) -> dict[str, Any] | None:
        """Post a single tweet.

        Args:
            text: Tweet text (max 280 chars).
            reply_to: ID of tweet to reply to (for threads).

        Returns:
            API response dict with tweet ID, or None on error.
        """
        if not self.bearer_token:
            self.log.error("twitter.no_bearer_token")
            return None

        try:
            payload: dict[str, Any] = {"text": text[:280]}
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}

            response = httpx.post(
                f"{TWITTER_API_BASE}/tweets",
                headers=self._get_oauth_headers(),
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()

            result = response.json()
            tweet_id = result.get("data", {}).get("id")

            self.log.info(
                "twitter.tweet_posted",
                tweet_id=tweet_id,
                length=len(text),
                is_reply=reply_to is not None,
            )

            return result

        except httpx.HTTPStatusError as exc:
            self.log.error(
                "twitter.api_error",
                status_code=exc.response.status_code,
                detail=exc.response.text[:200],
            )
            return None
        except Exception as exc:
            self.log.exception("twitter.error", error=str(exc))
            return None

    def post_thread(self, tweets: list[str]) -> list[dict[str, Any]]:
        """Post a thread (series of reply tweets).

        Args:
            tweets: List of tweet texts in order.

        Returns:
            List of API responses for each tweet.
        """
        if not tweets:
            return []

        results: list[dict[str, Any]] = []
        previous_tweet_id: str | None = None

        for i, tweet_text in enumerate(tweets):
            result = self.post_tweet(tweet_text, reply_to=previous_tweet_id)

            if result:
                results.append(result)
                previous_tweet_id = result.get("data", {}).get("id")
            else:
                self.log.error("twitter.thread_broken", tweet_index=i)
                break

            # Rate limit: wait between tweets
            if i < len(tweets) - 1:
                time.sleep(2)

        self.log.info(
            "twitter.thread_posted",
            total_tweets=len(tweets),
            posted=len(results),
        )

        return results

    def parse_thread_content(self, content: str) -> list[str]:
        """Parse generated thread content into individual tweets.

        Handles JSON array format or numbered list format.
        """
        import json

        # Try JSON array first
        try:
            tweets = json.loads(content)
            if isinstance(tweets, list):
                return [str(t).strip() for t in tweets if str(t).strip()]
        except (json.JSONDecodeError, TypeError):
            pass

        # Fall back to splitting by line/numbered format
        lines = content.strip().split("\n")
        tweets = []
        current = ""

        for line in lines:
            line = line.strip()
            if not line:
                if current:
                    tweets.append(current.strip())
                    current = ""
                continue

            # Check for numbered tweet markers
            import re
            if re.match(r"^\d+[./)]", line):
                if current:
                    tweets.append(current.strip())
                current = re.sub(r"^\d+[./)]\s*", "", line)
            else:
                current += " " + line if current else line

        if current:
            tweets.append(current.strip())

        return tweets

"""Dead Drop Pipeline — Publisher orchestrator.

Coordinates publishing approved content across all channels:
beehiiv, Twitter/X, Telegram, Reddit.
"""

from __future__ import annotations

from typing import Any

import structlog

from pipeline.config import settings
from pipeline.publishers.beehiiv import BeehiivPublisher
from pipeline.publishers.twitter import TwitterPublisher
from pipeline.publishers.telegram import TelegramPublisher
from pipeline.publishers.reddit import RedditPublisher

logger = structlog.get_logger()


class PublishResult:
    """Result of a multi-channel publish operation."""

    def __init__(self, story_title: str) -> None:
        self.story_title = story_title
        self.channels: dict[str, dict[str, Any]] = {}

    def add_result(self, channel: str, success: bool, detail: Any = None) -> None:
        self.channels[channel] = {
            "success": success,
            "detail": detail,
        }

    @property
    def all_success(self) -> bool:
        return all(ch["success"] for ch in self.channels.values())

    @property
    def summary(self) -> dict[str, bool]:
        return {ch: data["success"] for ch, data in self.channels.items()}


def publish_story(
    story: dict[str, Any],
    content_outputs: dict[str, str],
    channels: list[str] | None = None,
    dry_run: bool = False,
) -> PublishResult:
    """Publish a story across multiple channels.

    Args:
        story: Story dict with title, pillar, etc.
        content_outputs: Dict mapping output_type to content string.
        channels: List of channels to publish to. Defaults to all configured.
        dry_run: If True, log what would be published without actually publishing.

    Returns:
        PublishResult with per-channel results.
    """
    title = story.get("title", "Untitled")
    result = PublishResult(title)
    log = logger.bind(story_title=title[:80], dry_run=dry_run)

    if channels is None:
        channels = ["newsletter", "twitter", "telegram", "reddit"]

    log.info("publish.starting", channels=channels)

    # Newsletter (beehiiv)
    if "newsletter" in channels and "newsletter" in content_outputs:
        if dry_run:
            log.info("publish.dry_run", channel="beehiiv")
            result.add_result("beehiiv", True, "dry_run")
        elif settings.BEEHIIV_API_KEY:
            publisher = BeehiivPublisher()
            try:
                resp = publisher.create_post(
                    title=title,
                    content_html=content_outputs["newsletter"],
                    status="draft",
                )
                result.add_result("beehiiv", resp is not None, resp)
            finally:
                publisher.close()
        else:
            result.add_result("beehiiv", False, "not_configured")

    # Twitter thread
    if "twitter" in channels and "twitter_thread" in content_outputs:
        if dry_run:
            log.info("publish.dry_run", channel="twitter")
            result.add_result("twitter", True, "dry_run")
        elif settings.TWITTER_BEARER_TOKEN:
            publisher = TwitterPublisher()
            tweets = publisher.parse_thread_content(content_outputs["twitter_thread"])
            resp = publisher.post_thread(tweets)
            result.add_result("twitter", len(resp) > 0, {"tweets_posted": len(resp)})
        else:
            result.add_result("twitter", False, "not_configured")

    # Telegram
    if "telegram" in channels and "telegram" in content_outputs:
        if dry_run:
            log.info("publish.dry_run", channel="telegram")
            result.add_result("telegram", True, "dry_run")
        elif settings.TELEGRAM_BOT_TOKEN:
            publisher = TelegramPublisher()
            resp = publisher.send_message(content_outputs["telegram"])
            result.add_result("telegram", resp is not None, resp)
        else:
            result.add_result("telegram", False, "not_configured")

    # Reddit
    if "reddit" in channels and "reddit_post" in content_outputs:
        if dry_run:
            log.info("publish.dry_run", channel="reddit")
            result.add_result("reddit", True, "dry_run")
        elif settings.REDDIT_CLIENT_ID:
            publisher = RedditPublisher()
            resp = publisher.post_to_default_subs(
                title=title,
                text=content_outputs["reddit_post"],
            )
            result.add_result("reddit", True, resp)
        else:
            result.add_result("reddit", False, "not_configured")

    log.info("publish.complete", results=result.summary)
    return result

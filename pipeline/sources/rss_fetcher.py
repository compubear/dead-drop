"""Dead Drop Pipeline — RSS feed fetcher.

Fetches and parses RSS/Atom feeds, deduplicates entries,
and stores new items in the raw_items table.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
import structlog

from pipeline.sources.config_loader import SourceConfig

logger = structlog.get_logger()

# Default timeout for HTTP requests (seconds)
HTTP_TIMEOUT = 30.0

# User agent for polite fetching
USER_AGENT = "DeadDropBot/1.0 (+https://dead-drop.co)"


class FetchResult:
    """Result of a single feed fetch operation."""

    def __init__(
        self,
        source: SourceConfig,
        items: list[dict[str, Any]],
        status: str = "ok",
        error: str | None = None,
    ):
        self.source = source
        self.items = items
        self.status = status
        self.error = error

    @property
    def item_count(self) -> int:
        return len(self.items)


def compute_content_hash(title: str, url: str) -> str:
    """Compute SHA-256 hash for deduplication.

    Uses title + URL to generate a unique fingerprint.
    """
    content = f"{title.strip().lower()}|{url.strip().lower()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_published_date(entry: Any) -> datetime | None:
    """Extract and parse the published date from a feed entry.

    Handles various date formats common in RSS/Atom feeds.
    """
    date_fields = ["published_parsed", "updated_parsed", "created_parsed"]

    for field in date_fields:
        parsed = getattr(entry, field, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

    return None


def extract_content(entry: Any) -> str:
    """Extract the best available content from a feed entry.

    Prefers full content over summary, strips HTML if needed.
    """
    # Try content field first (Atom feeds)
    if hasattr(entry, "content") and entry.content:
        for content_item in entry.content:
            if hasattr(content_item, "value") and content_item.value:
                return content_item.value

    # Fall back to summary/description
    if hasattr(entry, "summary") and entry.summary:
        return entry.summary

    if hasattr(entry, "description") and entry.description:
        return entry.description

    return ""


def parse_entry(entry: Any, source: SourceConfig) -> dict[str, Any] | None:
    """Parse a single feed entry into a raw_item dict.

    Args:
        entry: feedparser entry object.
        source: Source configuration.

    Returns:
        Dict with raw_item fields, or None if entry is invalid.
    """
    title = getattr(entry, "title", "").strip()
    link = getattr(entry, "link", "").strip()

    if not title:
        return None

    content = extract_content(entry)
    published_at = parse_published_date(entry)
    content_hash = compute_content_hash(title, link or title)

    # Extract metadata
    metadata: dict[str, Any] = {}
    if hasattr(entry, "author") and entry.author:
        metadata["author"] = entry.author
    if hasattr(entry, "tags") and entry.tags:
        metadata["tags"] = [tag.get("term", "") for tag in entry.tags if isinstance(tag, dict)]
    metadata["source_name"] = source.name
    metadata["pillar"] = source.pillar

    return {
        "title": title,
        "content": content,
        "url": link,
        "published_at": published_at,
        "content_hash": content_hash,
        "external_id": link or content_hash,
        "metadata": metadata,
    }


def fetch_feed(source: SourceConfig) -> FetchResult:
    """Fetch and parse a single RSS/Atom feed.

    Args:
        source: Source configuration with URL and metadata.

    Returns:
        FetchResult with parsed items or error info.
    """
    log = logger.bind(source_name=source.name, source_url=source.url)
    log.info("rss.fetching")

    try:
        # Fetch with httpx for better timeout/error handling
        response = httpx.get(
            source.url,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        response.raise_for_status()

        # Parse with feedparser
        feed = feedparser.parse(response.text)

        if feed.bozo and feed.bozo_exception:
            log.warning(
                "rss.parse_warning",
                error=str(feed.bozo_exception),
            )

        items = []
        for entry in feed.entries:
            parsed = parse_entry(entry, source)
            if parsed:
                items.append(parsed)

        log.info("rss.fetched", items_found=len(items))
        return FetchResult(source=source, items=items)

    except httpx.TimeoutException:
        log.error("rss.timeout")
        return FetchResult(source=source, items=[], status="timeout", error="Request timed out")

    except httpx.HTTPStatusError as exc:
        log.error("rss.http_error", status_code=exc.response.status_code)
        return FetchResult(
            source=source,
            items=[],
            status="http_error",
            error=f"HTTP {exc.response.status_code}",
        )

    except Exception as exc:
        log.exception("rss.error", error=str(exc))
        return FetchResult(source=source, items=[], status="error", error=str(exc))


def fetch_multiple_feeds(sources: list[SourceConfig]) -> list[FetchResult]:
    """Fetch multiple feeds sequentially.

    Args:
        sources: List of source configurations.

    Returns:
        List of FetchResults.
    """
    results = []
    for source in sources:
        result = fetch_feed(source)
        results.append(result)

    total_items = sum(r.item_count for r in results)
    successes = sum(1 for r in results if r.status == "ok")
    failures = len(results) - successes

    logger.info(
        "rss.batch_complete",
        total_sources=len(sources),
        successes=successes,
        failures=failures,
        total_items=total_items,
    )

    return results

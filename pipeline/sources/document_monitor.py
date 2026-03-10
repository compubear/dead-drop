"""Dead Drop Pipeline — Document monitor.

Monitors specific pages for changes (new document uploads,
updated pages) by comparing page content hashes over time.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup
import structlog

from pipeline.sources.config_loader import SourceConfig

logger = structlog.get_logger()

USER_AGENT = "DeadDropBot/1.0 (+https://dead-drop.co)"
HTTP_TIMEOUT = 30.0

# In-memory page hash cache (will be moved to Redis in production)
_page_hash_cache: dict[str, str] = {}


def compute_page_hash(content: str) -> str:
    """Compute SHA-256 hash of cleaned page content."""
    # Strip whitespace and normalize for consistent hashing
    cleaned = " ".join(content.split())
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def has_page_changed(url: str, current_hash: str) -> bool:
    """Check if a page has changed since the last check.

    Args:
        url: Page URL (used as cache key).
        current_hash: Hash of current page content.

    Returns:
        True if page has changed or was never seen before.
    """
    previous_hash = _page_hash_cache.get(url)
    _page_hash_cache[url] = current_hash

    if previous_hash is None:
        # First time seeing this page
        return True

    return previous_hash != current_hash


def monitor_page(source: SourceConfig) -> list[dict[str, Any]]:
    """Monitor a page for new content/changes.

    Fetches the page, checks if content has changed,
    and extracts new items if a change is detected.

    Args:
        source: Source configuration with URL to monitor.

    Returns:
        List of raw_item dicts (empty if no changes detected).
    """
    log = logger.bind(source_name=source.name, source_url=source.url)
    log.info("document_monitor.checking")

    try:
        response = httpx.get(
            source.url,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Get main content area (strip nav, footer, etc.)
        main_content = soup.find("main") or soup.find("article") or soup.body
        if main_content is None:
            log.warning("document_monitor.no_content")
            return []

        content_text = main_content.get_text(separator=" ", strip=True)
        page_hash = compute_page_hash(content_text)

        if not has_page_changed(source.url, page_hash):
            log.info("document_monitor.no_changes")
            return []

        log.info("document_monitor.change_detected")

        # Extract document links from the page
        items = []
        for link in main_content.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Filter for document-like links
            is_document = any(
                ext in href.lower() for ext in [".pdf", ".doc", ".xlsx", ".csv"]
            )
            is_internal_link = len(text) > 15 and ("report" in text.lower() or "document" in text.lower() or "release" in text.lower())

            if not (is_document or is_internal_link):
                continue

            # Build full URL
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(source.url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"

            content_hash = hashlib.sha256(
                f"{text}|{href}".encode()
            ).hexdigest()

            items.append({
                "title": text or f"Document from {source.name}",
                "content": f"New document detected on {source.name}: {text}",
                "url": href,
                "published_at": datetime.now(timezone.utc),
                "content_hash": content_hash,
                "external_id": href,
                "metadata": {
                    "source_name": source.name,
                    "pillar": source.pillar,
                    "document_type": "monitored_page",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                },
            })

        log.info("document_monitor.items_found", count=len(items))
        return items

    except httpx.TimeoutException:
        log.error("document_monitor.timeout")
        return []
    except Exception as exc:
        log.exception("document_monitor.error", error=str(exc))
        return []

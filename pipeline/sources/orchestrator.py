"""Dead Drop Pipeline — Source monitoring orchestrator.

Coordinates all source monitoring activities:
RSS fetching, web scraping, and document monitoring.
Handles scheduling and error recovery.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from pipeline.sources.config_loader import (
    FeedConfig,
    SourceConfig,
    get_sources_by_type,
    load_feed_config,
)
from pipeline.sources.rss_fetcher import fetch_feed, FetchResult
from pipeline.sources.scraper import get_scraper
from pipeline.sources.document_monitor import monitor_page

logger = structlog.get_logger()


class MonitorResult:
    """Aggregate result of a full monitoring cycle."""

    def __init__(self) -> None:
        self.total_sources = 0
        self.sources_successful = 0
        self.sources_failed = 0
        self.items_found = 0
        self.items_new = 0
        self.items_duplicate = 0
        self.errors: list[dict[str, Any]] = []
        self.started_at = datetime.now(timezone.utc)
        self.completed_at: datetime | None = None

    def finalize(self) -> None:
        self.completed_at = datetime.now(timezone.utc)

    @property
    def duration_seconds(self) -> float:
        if self.completed_at is None:
            return 0
        return (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_sources": self.total_sources,
            "sources_successful": self.sources_successful,
            "sources_failed": self.sources_failed,
            "items_found": self.items_found,
            "items_new": self.items_new,
            "items_duplicate": self.items_duplicate,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
        }


def _process_rss_sources(sources: list[SourceConfig], result: MonitorResult) -> list[dict[str, Any]]:
    """Process all RSS sources."""
    all_items: list[dict[str, Any]] = []

    for source in sources:
        result.total_sources += 1
        fetch_result = fetch_feed(source)

        if fetch_result.status == "ok":
            result.sources_successful += 1
            result.items_found += fetch_result.item_count
            all_items.extend(fetch_result.items)
        else:
            result.sources_failed += 1
            result.errors.append({
                "source": source.name,
                "type": "rss",
                "error": fetch_result.error,
            })

    return all_items


def _process_scraper_sources(sources: list[SourceConfig], result: MonitorResult) -> list[dict[str, Any]]:
    """Process all scraper sources."""
    all_items: list[dict[str, Any]] = []

    for source in sources:
        result.total_sources += 1
        scraper = get_scraper(source)

        if scraper is None:
            result.sources_failed += 1
            result.errors.append({
                "source": source.name,
                "type": "scraper",
                "error": "No scraper implementation registered",
            })
            continue

        try:
            items = scraper.scrape()
            result.sources_successful += 1
            result.items_found += len(items)
            all_items.extend(items)
        except Exception as exc:
            result.sources_failed += 1
            result.errors.append({
                "source": source.name,
                "type": "scraper",
                "error": str(exc),
            })
        finally:
            scraper.close()

    return all_items


def _process_document_monitors(sources: list[SourceConfig], result: MonitorResult) -> list[dict[str, Any]]:
    """Process all document monitor sources."""
    all_items: list[dict[str, Any]] = []

    for source in sources:
        result.total_sources += 1

        try:
            items = monitor_page(source)
            result.sources_successful += 1
            result.items_found += len(items)
            all_items.extend(items)
        except Exception as exc:
            result.sources_failed += 1
            result.errors.append({
                "source": source.name,
                "type": "document_monitor",
                "error": str(exc),
            })

    return all_items


def run_monitoring_cycle(config: FeedConfig | None = None) -> MonitorResult:
    """Execute a full source monitoring cycle.

    Processes all configured sources: RSS feeds, web scrapers,
    and document monitors. Collects all items and reports
    aggregate statistics.

    Args:
        config: Feed configuration. If None, loads from default path.

    Returns:
        MonitorResult with all stats and items.
    """
    if config is None:
        config = load_feed_config()

    result = MonitorResult()

    logger.info(
        "monitor.cycle_starting",
        total_configured_sources=len(config.sources),
    )

    # Process by type
    rss_sources = get_sources_by_type(config, "rss")
    scraper_sources = get_sources_by_type(config, "scraper")
    monitor_sources = get_sources_by_type(config, "document_monitor")

    all_items: list[dict[str, Any]] = []

    # RSS feeds
    if rss_sources:
        logger.info("monitor.processing_rss", count=len(rss_sources))
        all_items.extend(_process_rss_sources(rss_sources, result))

    # Web scrapers
    if scraper_sources:
        logger.info("monitor.processing_scrapers", count=len(scraper_sources))
        all_items.extend(_process_scraper_sources(scraper_sources, result))

    # Document monitors
    if monitor_sources:
        logger.info("monitor.processing_monitors", count=len(monitor_sources))
        all_items.extend(_process_document_monitors(monitor_sources, result))

    result.finalize()

    logger.info(
        "monitor.cycle_complete",
        **result.to_dict(),
    )

    return result

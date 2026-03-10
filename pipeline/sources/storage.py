"""Dead Drop Pipeline — Item storage.

Persists raw ingested items to the database with deduplication.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog

from pipeline.db.connection import get_connection

logger = structlog.get_logger()


def store_raw_item(
    source_id: int,
    item: dict[str, Any],
) -> int | None:
    """Store a single raw item in the database.

    Uses content_hash for deduplication — skips if already exists.

    Args:
        source_id: ID of the source in the sources table.
        item: Raw item dict from fetcher/scraper.

    Returns:
        ID of the inserted row, or None if duplicate.
    """
    conn = get_connection()

    try:
        # Check for duplicate
        existing = conn.execute(
            "SELECT id FROM raw_items WHERE content_hash = %s",
            [item["content_hash"]],
        ).fetchone()

        if existing:
            return None

        # Insert new item
        row = conn.execute(
            """
            INSERT INTO raw_items (
                source_id, external_id, title, content, url,
                published_at, content_hash, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            [
                source_id,
                item.get("external_id", ""),
                item["title"],
                item.get("content", ""),
                item.get("url", ""),
                item.get("published_at"),
                item["content_hash"],
                json.dumps(item.get("metadata", {})),
            ],
        ).fetchone()

        conn.commit()

        if row:
            logger.debug(
                "storage.item_stored",
                item_id=row[0],
                title=item["title"][:80],
            )
            return row[0]

        return None

    except Exception as exc:
        conn.rollback()
        logger.error(
            "storage.store_error",
            error=str(exc),
            title=item.get("title", "unknown")[:80],
        )
        raise


def store_raw_items(
    source_id: int,
    items: list[dict[str, Any]],
) -> dict[str, int]:
    """Store multiple raw items with deduplication stats.

    Args:
        source_id: ID of the source in the sources table.
        items: List of raw item dicts.

    Returns:
        Dict with counts: {"stored": N, "duplicates": N, "errors": N}
    """
    stats = {"stored": 0, "duplicates": 0, "errors": 0}

    for item in items:
        try:
            result = store_raw_item(source_id, item)
            if result is not None:
                stats["stored"] += 1
            else:
                stats["duplicates"] += 1
        except Exception:
            stats["errors"] += 1

    logger.info(
        "storage.batch_complete",
        source_id=source_id,
        **stats,
    )

    return stats


def ensure_source_registered(
    name: str,
    url: str,
    source_type: str,
    pillar: str,
    fetch_interval: int = 60,
) -> int:
    """Ensure a source exists in the database, creating if needed.

    Args:
        name: Source name.
        url: Source URL.
        source_type: Type (rss, scraper, etc.).
        pillar: Content pillar.
        fetch_interval: Fetch interval in minutes.

    Returns:
        Source ID.
    """
    conn = get_connection()

    # Check if source exists
    row = conn.execute(
        "SELECT id FROM sources WHERE name = %s",
        [name],
    ).fetchone()

    if row:
        return row[0]

    # Create source
    row = conn.execute(
        """
        INSERT INTO sources (name, url, source_type, pillar, fetch_interval_minutes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        [name, url, source_type, pillar, fetch_interval],
    ).fetchone()

    conn.commit()

    source_id = row[0]
    logger.info(
        "storage.source_registered",
        source_id=source_id,
        source_name=name,
    )

    return source_id


def update_source_last_fetched(source_id: int) -> None:
    """Update the last_fetched_at timestamp for a source."""
    conn = get_connection()
    conn.execute(
        "UPDATE sources SET last_fetched_at = %s WHERE id = %s",
        [datetime.now(timezone.utc), source_id],
    )
    conn.commit()

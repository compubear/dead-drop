"""Dead Drop Pipeline — Story persistence.

Stores scored stories and manages their lifecycle
from scoring through to publication.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog

from pipeline.db.connection import get_connection

logger = structlog.get_logger()


def create_story(
    raw_item_ids: list[int],
    title: str,
    summary: str,
    pillar: str,
    significance_score: float,
    coverage_score: float,
    scoring_reasoning: str,
    metadata: dict[str, Any] | None = None,
) -> int | None:
    """Create a new story from scored raw items.

    Args:
        raw_item_ids: IDs of source raw_items.
        title: Story title (from scoring or manual).
        summary: Story summary.
        pillar: Content pillar.
        significance_score: 1-10 significance rating.
        coverage_score: 1-10 coverage rating.
        scoring_reasoning: Claude's reasoning text.
        metadata: Additional metadata.

    Returns:
        Story ID if created, None on error.
    """
    conn = get_connection()

    try:
        row = conn.execute(
            """
            INSERT INTO stories (
                raw_item_ids, title, summary, pillar,
                significance_score, coverage_score,
                scoring_reasoning, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            [
                raw_item_ids,
                title,
                summary,
                pillar,
                significance_score,
                coverage_score,
                scoring_reasoning,
                json.dumps(metadata or {}),
            ],
        ).fetchone()

        conn.commit()

        if row:
            logger.info(
                "story.created",
                story_id=row[0],
                title=title[:80],
                gap_score=significance_score - coverage_score,
            )
            return row[0]

        return None

    except Exception as exc:
        conn.rollback()
        logger.error("story.create_error", error=str(exc))
        raise


def update_story_status(story_id: int, status: str) -> None:
    """Update the status of a story.

    Status flow: scored → selected → in_progress → verified → published | rejected
    """
    conn = get_connection()
    conn.execute(
        "UPDATE stories SET status = %s WHERE id = %s",
        [status, story_id],
    )
    conn.commit()
    logger.info("story.status_updated", story_id=story_id, status=status)


def get_top_stories(
    limit: int = 10,
    min_gap_score: float = 3.0,
    status: str = "scored",
) -> list[dict[str, Any]]:
    """Get top stories by gap score.

    Args:
        limit: Max stories to return.
        min_gap_score: Minimum gap score threshold.
        status: Filter by status.

    Returns:
        List of story dicts.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, title, summary, pillar,
               significance_score, coverage_score, gap_score,
               scoring_reasoning, status, metadata, created_at
        FROM stories
        WHERE status = %s AND gap_score >= %s
        ORDER BY gap_score DESC
        LIMIT %s
        """,
        [status, min_gap_score, limit],
    ).fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "summary": row[2],
            "pillar": row[3],
            "significance_score": row[4],
            "coverage_score": row[5],
            "gap_score": row[6],
            "scoring_reasoning": row[7],
            "status": row[8],
            "metadata": row[9],
            "created_at": row[10],
        }
        for row in rows
    ]

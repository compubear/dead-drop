"""Dead Drop Pipeline — Content output storage.

Persists generated content to the database and manages
the content lifecycle (draft → reviewed → approved → published).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog

from pipeline.db.connection import get_connection

logger = structlog.get_logger()


def store_content_output(
    story_id: int,
    output_type: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> int | None:
    """Store a generated content output.

    Args:
        story_id: ID of the source story.
        output_type: Content type (newsletter, twitter_thread, etc.).
        content: Generated content text.
        metadata: Additional metadata (model, generation params).

    Returns:
        Content output ID, or None on error.
    """
    conn = get_connection()

    try:
        row = conn.execute(
            """
            INSERT INTO content_outputs (story_id, output_type, content, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            [story_id, output_type, content, json.dumps(metadata or {})],
        ).fetchone()

        conn.commit()

        if row:
            logger.info(
                "content_output.stored",
                output_id=row[0],
                story_id=story_id,
                type=output_type,
            )
            return row[0]
        return None

    except Exception as exc:
        conn.rollback()
        logger.error("content_output.store_error", error=str(exc))
        raise


def update_content_status(
    output_id: int,
    status: str,
    published_url: str | None = None,
) -> None:
    """Update the status of a content output.

    Status flow: draft → reviewed → approved → published
    """
    conn = get_connection()

    params: list[Any] = [status]
    query = "UPDATE content_outputs SET status = %s"

    if status == "published" and published_url:
        query += ", published_url = %s, published_at = %s"
        params.extend([published_url, datetime.now(timezone.utc)])

    query += " WHERE id = %s"
    params.append(output_id)

    conn.execute(query, params)
    conn.commit()

    logger.info(
        "content_output.status_updated",
        output_id=output_id,
        status=status,
    )


def get_outputs_for_story(story_id: int) -> list[dict[str, Any]]:
    """Get all content outputs for a story."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, output_type, content, status, published_url,
               metadata, created_at, published_at
        FROM content_outputs
        WHERE story_id = %s
        ORDER BY created_at DESC
        """,
        [story_id],
    ).fetchall()

    return [
        {
            "id": row[0],
            "output_type": row[1],
            "content": row[2],
            "status": row[3],
            "published_url": row[4],
            "metadata": row[5],
            "created_at": row[6],
            "published_at": row[7],
        }
        for row in rows
    ]


def get_pending_publications(
    output_type: str | None = None,
) -> list[dict[str, Any]]:
    """Get content outputs that are approved but not yet published."""
    conn = get_connection()

    query = """
        SELECT co.id, co.story_id, co.output_type, co.content,
               s.title as story_title, s.pillar
        FROM content_outputs co
        JOIN stories s ON s.id = co.story_id
        WHERE co.status = 'approved'
    """
    params: list[Any] = []

    if output_type:
        query += " AND co.output_type = %s"
        params.append(output_type)

    query += " ORDER BY s.gap_score DESC"

    rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": row[0],
            "story_id": row[1],
            "output_type": row[2],
            "content": row[3],
            "story_title": row[4],
            "pillar": row[5],
        }
        for row in rows
    ]

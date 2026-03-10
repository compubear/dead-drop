"""Dead Drop Pipeline — Database connection helper."""

from __future__ import annotations

import psycopg
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

_connection: psycopg.Connection | None = None


def get_connection(autocommit: bool = False) -> psycopg.Connection:
    """Get or create a database connection.

    Args:
        autocommit: If True, connection operates in autocommit mode.

    Returns:
        Active psycopg connection.
    """
    global _connection

    if _connection is None or _connection.closed:
        logger.debug("db.connecting", host=settings.POSTGRES_HOST, db=settings.POSTGRES_DB)
        _connection = psycopg.connect(
            settings.database_url,
            autocommit=autocommit,
        )
        logger.info("db.connected", host=settings.POSTGRES_HOST, db=settings.POSTGRES_DB)

    return _connection


def close_connection() -> None:
    """Close the database connection if open."""
    global _connection
    if _connection and not _connection.closed:
        _connection.close()
        _connection = None
        logger.info("db.disconnected")


def execute_query(
    query: str,
    params: list | tuple | None = None,
    fetch: bool = False,
) -> list[tuple] | None:
    """Execute a query with optional parameter binding.

    Args:
        query: SQL query string.
        params: Query parameters.
        fetch: If True, fetch and return all rows.

    Returns:
        List of result tuples if fetch=True, else None.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(query, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return None
    except Exception:
        conn.rollback()
        raise

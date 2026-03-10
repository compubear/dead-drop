"""Dead Drop — Database migration runner."""

import os
import sys
from pathlib import Path

import psycopg
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_connection() -> psycopg.Connection:
    """Create a database connection."""
    return psycopg.connect(settings.database_url)


def ensure_migrations_table(conn: psycopg.Connection) -> None:
    """Create the migrations tracking table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()


def get_applied_migrations(conn: psycopg.Connection) -> set[str]:
    """Get the set of already-applied migration filenames."""
    rows = conn.execute("SELECT filename FROM _migrations ORDER BY id").fetchall()
    return {row[0] for row in rows}


def run_migrations() -> None:
    """Run all pending database migrations in order."""
    if not MIGRATIONS_DIR.exists():
        logger.warning("migrations.dir_not_found", path=str(MIGRATIONS_DIR))
        return

    migration_files = sorted(
        f for f in MIGRATIONS_DIR.iterdir() if f.suffix == ".sql"
    )

    if not migration_files:
        logger.info("migrations.none_found")
        return

    conn = get_connection()
    ensure_migrations_table(conn)
    applied = get_applied_migrations(conn)

    pending = [f for f in migration_files if f.name not in applied]

    if not pending:
        logger.info("migrations.up_to_date", applied_count=len(applied))
        return

    logger.info("migrations.pending", count=len(pending))

    for migration_file in pending:
        logger.info("migrations.applying", filename=migration_file.name)
        sql = migration_file.read_text()

        try:
            conn.execute(sql)
            conn.execute(
                "INSERT INTO _migrations (filename) VALUES (%s)",
                [migration_file.name],
            )
            conn.commit()
            logger.info("migrations.applied", filename=migration_file.name)
        except Exception as exc:
            conn.rollback()
            logger.error(
                "migrations.failed",
                filename=migration_file.name,
                error=str(exc),
            )
            raise

    conn.close()
    logger.info("migrations.complete", total_applied=len(pending))


if __name__ == "__main__":
    run_migrations()

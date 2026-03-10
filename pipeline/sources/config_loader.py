"""Dead Drop Pipeline — Source configuration loader.

Loads feed/source definitions from config/feeds.yaml,
validates them, and provides sync-to-DB functionality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
import structlog
from pydantic import BaseModel, HttpUrl, field_validator

logger = structlog.get_logger()

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "feeds.yaml"

PillarType = Literal["intelligence", "conflicts", "ai", "cyber", "historical"]
SourceType = Literal["rss", "scraper", "api", "document_monitor"]


class SourceConfig(BaseModel):
    """A single source definition from feeds.yaml."""

    name: str
    url: str
    type: SourceType
    pillar: PillarType
    interval: int = 60  # fetch interval in minutes

    @field_validator("interval")
    @classmethod
    def interval_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("interval must be >= 1 minute")
        return v


class FeedConfig(BaseModel):
    """Top-level feed configuration."""

    sources: list[SourceConfig]


def load_feed_config(config_path: Path | None = None) -> FeedConfig:
    """Load and validate the feeds.yaml configuration.

    Args:
        config_path: Path to feeds.yaml. Defaults to config/feeds.yaml.

    Returns:
        Validated FeedConfig object.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is invalid.
    """
    path = config_path or CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Feed config not found: {path}")

    raw = yaml.safe_load(path.read_text())
    config = FeedConfig(**raw)

    # Log summary by pillar
    pillar_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    for src in config.sources:
        pillar_counts[src.pillar] = pillar_counts.get(src.pillar, 0) + 1
        type_counts[src.type] = type_counts.get(src.type, 0) + 1

    logger.info(
        "sources.config_loaded",
        total=len(config.sources),
        by_pillar=pillar_counts,
        by_type=type_counts,
        config_path=str(path),
    )

    return config


def get_sources_by_type(
    config: FeedConfig, source_type: SourceType
) -> list[SourceConfig]:
    """Filter sources by type (rss, scraper, etc.)."""
    return [s for s in config.sources if s.type == source_type]


def get_sources_by_pillar(
    config: FeedConfig, pillar: PillarType
) -> list[SourceConfig]:
    """Filter sources by content pillar."""
    return [s for s in config.sources if s.pillar == pillar]

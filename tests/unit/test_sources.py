"""Dead Drop — Sprint 1 tests: Source monitoring engine."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from pipeline.sources.config_loader import (
    SourceConfig,
    FeedConfig,
    load_feed_config,
    get_sources_by_type,
    get_sources_by_pillar,
)
from pipeline.sources.rss_fetcher import (
    compute_content_hash,
    parse_entry,
    FetchResult,
)
from pipeline.sources.scraper import BaseScraper, SCRAPER_REGISTRY, get_scraper
from pipeline.sources.document_monitor import compute_page_hash, has_page_changed, _page_hash_cache
from pipeline.sources.orchestrator import MonitorResult


# === Config Loader Tests ===

class TestConfigLoader:
    """Test feed configuration loading and validation."""

    def test_load_real_config(self):
        """Test loading the actual feeds.yaml file."""
        config = load_feed_config()
        assert len(config.sources) > 0
        assert all(isinstance(s, SourceConfig) for s in config.sources)

    def test_source_config_validation(self):
        """Test SourceConfig validates correctly."""
        src = SourceConfig(
            name="Test Feed",
            url="https://example.com/feed",
            type="rss",
            pillar="intelligence",
            interval=120,
        )
        assert src.name == "Test Feed"
        assert src.type == "rss"
        assert src.pillar == "intelligence"
        assert src.interval == 120

    def test_invalid_pillar_rejected(self):
        """Test that invalid pillar values are rejected."""
        with pytest.raises(Exception):
            SourceConfig(
                name="Bad Feed",
                url="https://example.com",
                type="rss",
                pillar="invalid_pillar",  # type: ignore
                interval=60,
            )

    def test_invalid_source_type_rejected(self):
        """Test that invalid source types are rejected."""
        with pytest.raises(Exception):
            SourceConfig(
                name="Bad Feed",
                url="https://example.com",
                type="invalid_type",  # type: ignore
                pillar="ai",
                interval=60,
            )

    def test_invalid_interval_rejected(self):
        """Test that zero/negative intervals are rejected."""
        with pytest.raises(Exception):
            SourceConfig(
                name="Bad Feed",
                url="https://example.com",
                type="rss",
                pillar="ai",
                interval=0,
            )

    def test_filter_by_type(self):
        """Test filtering sources by type."""
        config = load_feed_config()
        rss_sources = get_sources_by_type(config, "rss")
        assert all(s.type == "rss" for s in rss_sources)
        assert len(rss_sources) > 0

    def test_filter_by_pillar(self):
        """Test filtering sources by pillar."""
        config = load_feed_config()
        intel_sources = get_sources_by_pillar(config, "intelligence")
        assert all(s.pillar == "intelligence" for s in intel_sources)

    def test_all_pillars_covered(self):
        """Test that all 5 pillars have at least one source."""
        config = load_feed_config()
        pillars_present = {s.pillar for s in config.sources}
        expected = {"intelligence", "conflicts", "ai", "cyber", "historical"}
        assert pillars_present == expected

    def test_config_file_not_found(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_feed_config(Path("/nonexistent/feeds.yaml"))


# === RSS Fetcher Tests ===

class TestRSSFetcher:
    """Test RSS feed fetching and parsing."""

    def test_content_hash_deterministic(self):
        """Test that content hash is consistent."""
        h1 = compute_content_hash("Test Title", "https://example.com")
        h2 = compute_content_hash("Test Title", "https://example.com")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_content_hash_case_insensitive(self):
        """Test that content hash normalizes case."""
        h1 = compute_content_hash("Test Title", "https://Example.com")
        h2 = compute_content_hash("test title", "https://example.com")
        assert h1 == h2

    def test_content_hash_strips_whitespace(self):
        """Test that content hash strips whitespace."""
        h1 = compute_content_hash("  Test Title  ", "  https://example.com  ")
        h2 = compute_content_hash("Test Title", "https://example.com")
        assert h1 == h2

    def test_different_content_different_hash(self):
        """Test that different content produces different hashes."""
        h1 = compute_content_hash("Title A", "https://example.com/a")
        h2 = compute_content_hash("Title B", "https://example.com/b")
        assert h1 != h2

    def test_parse_entry_basic(self):
        """Test parsing a basic feed entry."""
        source = SourceConfig(
            name="Test",
            url="https://example.com",
            type="rss",
            pillar="ai",
        )
        entry = MagicMock()
        entry.title = "Test Article"
        entry.link = "https://example.com/article"
        entry.summary = "Test summary"
        entry.author = "John Doe"
        entry.tags = []
        entry.published_parsed = (2024, 1, 15, 12, 0, 0, 0, 0, 0)
        # Ensure content is not set
        entry.content = None

        result = parse_entry(entry, source)
        assert result is not None
        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com/article"
        assert result["content"] == "Test summary"
        assert "content_hash" in result
        assert result["metadata"]["source_name"] == "Test"
        assert result["metadata"]["pillar"] == "ai"

    def test_parse_entry_no_title(self):
        """Test that entries without titles are rejected."""
        source = SourceConfig(
            name="Test",
            url="https://example.com",
            type="rss",
            pillar="ai",
        )
        entry = MagicMock()
        entry.title = ""
        entry.link = "https://example.com"

        result = parse_entry(entry, source)
        assert result is None

    def test_fetch_result_item_count(self):
        """Test FetchResult item count property."""
        source = SourceConfig(
            name="Test",
            url="https://example.com",
            type="rss",
            pillar="ai",
        )
        result = FetchResult(source=source, items=[{"a": 1}, {"b": 2}])
        assert result.item_count == 2

    def test_fetch_result_error(self):
        """Test FetchResult with error status."""
        source = SourceConfig(
            name="Test",
            url="https://example.com",
            type="rss",
            pillar="ai",
        )
        result = FetchResult(
            source=source, items=[], status="timeout", error="Request timed out"
        )
        assert result.status == "timeout"
        assert result.error == "Request timed out"
        assert result.item_count == 0


# === Document Monitor Tests ===

class TestDocumentMonitor:
    """Test document monitoring functionality."""

    def test_page_hash_deterministic(self):
        """Test that page hash is consistent."""
        h1 = compute_page_hash("Hello world test content")
        h2 = compute_page_hash("Hello world test content")
        assert h1 == h2

    def test_page_hash_normalizes_whitespace(self):
        """Test that page hash normalizes whitespace."""
        h1 = compute_page_hash("Hello   world\n\ttest")
        h2 = compute_page_hash("Hello world test")
        assert h1 == h2

    def test_page_changed_first_check(self):
        """Test that first check always returns True."""
        _page_hash_cache.clear()
        result = has_page_changed("https://unique-test-url.com/first", "hash123")
        assert result is True

    def test_page_changed_same_content(self):
        """Test that same content returns False."""
        _page_hash_cache.clear()
        has_page_changed("https://unique-test-url.com/same", "hash_same_123")
        result = has_page_changed("https://unique-test-url.com/same", "hash_same_123")
        assert result is False

    def test_page_changed_different_content(self):
        """Test that different content returns True."""
        _page_hash_cache.clear()
        has_page_changed("https://unique-test-url.com/diff", "hash_old")
        result = has_page_changed("https://unique-test-url.com/diff", "hash_new")
        assert result is True


# === Scraper Tests ===

class TestScraper:
    """Test web scraper functionality."""

    def test_scraper_registry_has_entries(self):
        """Test that scraper registry has registered scrapers."""
        assert len(SCRAPER_REGISTRY) > 0
        assert "CIA FOIA Reading Room" in SCRAPER_REGISTRY

    def test_get_scraper_known(self):
        """Test getting a registered scraper."""
        source = SourceConfig(
            name="CIA FOIA Reading Room",
            url="https://www.cia.gov/readingroom/collection",
            type="scraper",
            pillar="intelligence",
        )
        scraper = get_scraper(source)
        assert scraper is not None

    def test_get_scraper_unknown(self):
        """Test getting an unregistered scraper returns None."""
        source = SourceConfig(
            name="Unknown Source",
            url="https://example.com",
            type="scraper",
            pillar="ai",
        )
        scraper = get_scraper(source)
        assert scraper is None

    def test_base_scraper_compute_hash(self):
        """Test BaseScraper static hash method."""
        h = BaseScraper.compute_hash("Test", "https://example.com")
        assert isinstance(h, str)
        assert len(h) == 64


# === Orchestrator Tests ===

class TestOrchestrator:
    """Test monitoring orchestrator."""

    def test_monitor_result_initialization(self):
        """Test MonitorResult initializes correctly."""
        result = MonitorResult()
        assert result.total_sources == 0
        assert result.sources_successful == 0
        assert result.sources_failed == 0
        assert result.items_found == 0
        assert result.errors == []

    def test_monitor_result_finalize(self):
        """Test MonitorResult finalization sets completion time."""
        result = MonitorResult()
        result.total_sources = 5
        result.sources_successful = 4
        result.sources_failed = 1
        result.finalize()
        assert result.completed_at is not None
        assert result.duration_seconds >= 0

    def test_monitor_result_to_dict(self):
        """Test MonitorResult serialization."""
        result = MonitorResult()
        result.total_sources = 10
        result.items_found = 50
        result.finalize()
        d = result.to_dict()
        assert d["total_sources"] == 10
        assert d["items_found"] == 50
        assert "duration_seconds" in d

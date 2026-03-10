"""Dead Drop Pipeline — Web scraper module.

Base scraper class using httpx + BeautifulSoup for sources
that don't provide RSS feeds (government archives, document repos, etc.).
"""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup
import structlog

from pipeline.sources.config_loader import SourceConfig

logger = structlog.get_logger()

USER_AGENT = "DeadDropBot/1.0 (+https://dead-drop.co)"
HTTP_TIMEOUT = 30.0
POLITE_DELAY = 3.0  # seconds between requests to same domain


class BaseScraper(ABC):
    """Base class for all Dead Drop web scrapers.

    Subclasses must implement `parse_page()` to extract items
    from a specific source's HTML structure.
    """

    def __init__(self, source: SourceConfig):
        self.source = source
        self.log = logger.bind(
            source_name=source.name,
            source_url=source.url,
        )
        self.client = httpx.Client(
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    def fetch_page(self, url: str | None = None) -> BeautifulSoup | None:
        """Fetch a page and return parsed BeautifulSoup object.

        Args:
            url: URL to fetch. Defaults to source URL.

        Returns:
            BeautifulSoup object or None on error.
        """
        target_url = url or self.source.url
        self.log.info("scraper.fetching", url=target_url)

        try:
            response = self.client.get(target_url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except httpx.TimeoutException:
            self.log.error("scraper.timeout", url=target_url)
            return None
        except httpx.HTTPStatusError as exc:
            self.log.error("scraper.http_error", status_code=exc.response.status_code)
            return None
        except Exception as exc:
            self.log.exception("scraper.error", error=str(exc))
            return None

    @abstractmethod
    def parse_page(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse a page and extract items.

        Args:
            soup: Parsed HTML page.

        Returns:
            List of raw_item dicts.
        """
        ...

    def scrape(self) -> list[dict[str, Any]]:
        """Execute the full scrape operation.

        Returns:
            List of raw_item dicts.
        """
        soup = self.fetch_page()
        if soup is None:
            return []

        items = self.parse_page(soup)
        self.log.info("scraper.complete", items_found=len(items))
        return items

    @staticmethod
    def compute_hash(title: str, url: str) -> str:
        """Compute content hash for deduplication."""
        content = f"{title.strip().lower()}|{url.strip().lower()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def polite_delay(self) -> None:
        """Wait between requests to be polite to servers."""
        time.sleep(POLITE_DELAY)

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()


class CIAFOIAScraper(BaseScraper):
    """Scraper for CIA FOIA Electronic Reading Room.

    Monitors the CIA's public FOIA collection page for new
    document releases and declassified collections.
    """

    def parse_page(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        items = []
        # Find collection links on the FOIA page
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Filter for collection/document links
            if not text or len(text) < 10:
                continue
            if "/readingroom/" not in href and "/collection/" not in href:
                continue

            # Build full URL if relative
            if href.startswith("/"):
                href = f"https://www.cia.gov{href}"

            items.append({
                "title": text,
                "content": f"CIA FOIA document: {text}",
                "url": href,
                "published_at": datetime.now(timezone.utc),
                "content_hash": self.compute_hash(text, href),
                "external_id": href,
                "metadata": {
                    "source_name": self.source.name,
                    "pillar": "intelligence",
                    "document_type": "foia",
                },
            })

        return items


class NARAScraper(BaseScraper):
    """Scraper for National Archives (NARA) new releases.

    Monitors NARA for newly declassified documents and releases.
    """

    def parse_page(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        items = []

        for article in soup.find_all("article"):
            title_el = article.find(["h2", "h3", "h4"])
            link_el = article.find("a", href=True)

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            url = ""
            if link_el:
                href = link_el.get("href", "")
                url = href if href.startswith("http") else f"https://www.archives.gov{href}"

            # Get description/summary
            desc_el = article.find("p")
            content = desc_el.get_text(strip=True) if desc_el else ""

            items.append({
                "title": title,
                "content": content,
                "url": url,
                "published_at": datetime.now(timezone.utc),
                "content_hash": self.compute_hash(title, url or title),
                "external_id": url or self.compute_hash(title, "nara"),
                "metadata": {
                    "source_name": self.source.name,
                    "pillar": "historical",
                    "document_type": "archive",
                },
            })

        return items


# Registry of available scrapers by source name
SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "CIA FOIA Reading Room": CIAFOIAScraper,
    "NARA Latest Releases": NARAScraper,
}


def get_scraper(source: SourceConfig) -> BaseScraper | None:
    """Get the appropriate scraper for a source.

    Args:
        source: Source configuration.

    Returns:
        Scraper instance or None if no scraper is registered.
    """
    scraper_class = SCRAPER_REGISTRY.get(source.name)
    if scraper_class is None:
        logger.warning("scraper.no_implementation", source_name=source.name)
        return None
    return scraper_class(source)

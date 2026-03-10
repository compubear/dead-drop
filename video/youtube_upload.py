"""Dead Drop Pipeline — YouTube uploader.

Uploads videos and thumbnails to YouTube via the YouTube Data API v3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# Dead Drop YouTube category: News & Politics
CATEGORY_NEWS = "25"

# Standard Dead Drop video tags
DEFAULT_TAGS = [
    "dead drop",
    "intelligence",
    "geopolitics",
    "OSINT",
    "national security",
    "declassified",
    "espionage",
    "cybersecurity",
    "AI",
    "underreported news",
]


class YouTubeUploader:
    """Uploads videos to YouTube."""

    def __init__(self) -> None:
        self.api_key = settings.YOUTUBE_API_KEY
        self.log = logger.bind(module="youtube_uploader")

        if not self.api_key:
            self.log.warning("youtube.not_configured")

    def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str] | None = None,
        privacy: str = "unlisted",
        category: str = CATEGORY_NEWS,
    ) -> dict[str, Any] | None:
        """Upload a video to YouTube.

        Note: Full OAuth2 flow is required for uploads.
        This method prepares the metadata; actual upload requires
        google-api-python-client with OAuth2 credentials.

        Args:
            video_path: Path to the video file.
            title: Video title.
            description: Video description.
            tags: Video tags. Defaults to Dead Drop standard tags.
            privacy: 'public', 'unlisted', or 'private'.
            category: YouTube category ID.

        Returns:
            Upload result dict, or None on error.
        """
        if not video_path.exists():
            self.log.error("youtube.video_not_found", path=str(video_path))
            return None

        all_tags = (tags or []) + DEFAULT_TAGS

        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": all_tags[:30],  # YouTube max 30 tags
                "categoryId": category,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        self.log.info(
            "youtube.upload_prepared",
            title=title[:80],
            privacy=privacy,
            video_size_mb=round(video_path.stat().st_size / (1024 * 1024), 1),
        )

        # Note: Actual upload requires google-api-python-client
        # This returns the prepared metadata for now
        return {
            "status": "prepared",
            "metadata": metadata,
            "video_path": str(video_path),
            "note": "Requires google-api-python-client OAuth2 for actual upload",
        }

    def build_description(
        self,
        story_title: str,
        story_summary: str,
        sources: list[str] | None = None,
    ) -> str:
        """Build a standard Dead Drop video description.

        Args:
            story_title: Story title.
            story_summary: Story summary/context.
            sources: List of source URLs.

        Returns:
            Formatted YouTube description.
        """
        desc = f"""🔴 DEAD DROP — {story_title}

{story_summary}

━━━━━━━━━━━━━━━━━━━━━━━━
📧 Newsletter: https://dead-drop.co
🐦 Twitter: https://twitter.com/DeadDropIntel
📱 Telegram: https://t.me/DeadDropIntel
━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ DISCLAIMER: Dead Drop is an AI-assisted investigative media project.
All content undergoes a 5-point verification protocol.
We report facts, not speculation.

"""

        if sources:
            desc += "📎 SOURCES:\n"
            for i, source in enumerate(sources, 1):
                desc += f"{i}. {source}\n"

        desc += "\n#DeadDrop #Intelligence #Geopolitics #OSINT #Declassified"

        return desc

"""Dead Drop Pipeline — ElevenLabs narration generator.

Generates AI voice narration using ElevenLabs text-to-speech API.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

import httpx
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

# Dead Drop preferred voice settings
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.75,
    "similarity_boost": 0.75,
    "style": 0.2,
    "use_speaker_boost": True,
}

# Male news anchor-style voice
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam (deep, authoritative)


class NarrationGenerator:
    """Generates AI narration audio using ElevenLabs."""

    def __init__(self, voice_id: str = DEFAULT_VOICE_ID) -> None:
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = voice_id
        self.log = logger.bind(module="narration")

        if not self.api_key:
            self.log.warning("narration.not_configured")

    def generate_narration(
        self,
        text: str,
        output_path: Path,
        model: str = "eleven_multilingual_v2",
    ) -> Path | None:
        """Generate narration audio from text.

        Args:
            text: Script text to narrate.
            output_path: Path to save the audio file (.mp3).
            model: ElevenLabs model to use.

        Returns:
            Path to the generated audio file, or None on error.
        """
        if not self.api_key:
            self.log.error("narration.no_api_key")
            return None

        self.log.info("narration.generating", text_length=len(text))

        try:
            response = httpx.post(
                f"{ELEVENLABS_API_BASE}/text-to-speech/{self.voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": text,
                    "model_id": model,
                    "voice_settings": DEFAULT_VOICE_SETTINGS,
                },
                timeout=120.0,
            )
            response.raise_for_status()

            # Write audio to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)

            self.log.info(
                "narration.generated",
                output_path=str(output_path),
                size_bytes=len(response.content),
            )

            return output_path

        except httpx.HTTPStatusError as exc:
            self.log.error(
                "narration.api_error",
                status_code=exc.response.status_code,
                detail=exc.response.text[:200],
            )
            return None
        except Exception as exc:
            self.log.exception("narration.error", error=str(exc))
            return None

    def get_available_voices(self) -> list[dict[str, Any]]:
        """List available voices from ElevenLabs."""
        if not self.api_key:
            return []

        try:
            response = httpx.get(
                f"{ELEVENLABS_API_BASE}/voices",
                headers={"xi-api-key": self.api_key},
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json().get("voices", [])
        except Exception as exc:
            self.log.exception("narration.voices_error", error=str(exc))
            return []

    def estimate_duration(self, text: str) -> float:
        """Estimate narration duration in seconds.

        Average speaking rate: ~150 words per minute.
        """
        word_count = len(text.split())
        return (word_count / 150) * 60

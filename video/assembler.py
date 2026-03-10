"""Dead Drop Pipeline — Video assembler.

Assembles Dead Drop video episodes from:
- AI narration audio (ElevenLabs)
- Background/B-roll footage
- Maps and document overlays
- Branded intro/outro
- Subtitles/captions

Uses MoviePy for video composition.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# Video output settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920

# Brand colors for overlays
BRAND_BLACK = (15, 15, 15)
BRAND_RED = (220, 38, 38)
BRAND_WHITE = (245, 245, 245)
BRAND_STEEL = (148, 163, 184)

# Asset paths
ASSETS_DIR = Path(__file__).parent / "assets"


class VideoProject:
    """Represents a single video production project."""

    def __init__(
        self,
        title: str,
        output_dir: Path,
        format: str = "standard",  # "standard" (16:9) or "shorts" (9:16)
    ) -> None:
        self.title = title
        self.output_dir = output_dir
        self.format = format
        self.log = logger.bind(video_title=title[:60])

        self.width = SHORTS_WIDTH if format == "shorts" else VIDEO_WIDTH
        self.height = SHORTS_HEIGHT if format == "shorts" else VIDEO_HEIGHT

        # Track project components
        self.narration_path: Path | None = None
        self.scenes: list[dict[str, Any]] = []
        self.subtitles: list[dict[str, Any]] = []

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def set_narration(self, audio_path: Path) -> None:
        """Set the narration audio track."""
        if not audio_path.exists():
            self.log.error("video.narration_not_found", path=str(audio_path))
            return
        self.narration_path = audio_path
        self.log.info("video.narration_set", path=str(audio_path))

    def add_scene(
        self,
        scene_type: str,
        duration: float,
        content: dict[str, Any],
    ) -> None:
        """Add a scene to the video timeline.

        Args:
            scene_type: Type of scene (title_card, b_roll, map, document, text_overlay).
            duration: Duration in seconds.
            content: Scene-specific content dict.
        """
        self.scenes.append({
            "type": scene_type,
            "duration": duration,
            "content": content,
            "index": len(self.scenes),
        })
        self.log.debug(
            "video.scene_added",
            scene_type=scene_type,
            duration=duration,
            index=len(self.scenes) - 1,
        )

    def add_title_card(self, title: str, subtitle: str = "", duration: float = 5.0) -> None:
        """Add a branded title card scene."""
        self.add_scene("title_card", duration, {
            "title": title,
            "subtitle": subtitle,
            "bg_color": BRAND_BLACK,
            "title_color": BRAND_WHITE,
            "accent_color": BRAND_RED,
        })

    def add_text_overlay(
        self, text: str, duration: float = 8.0, position: str = "center"
    ) -> None:
        """Add a text overlay scene for key points."""
        self.add_scene("text_overlay", duration, {
            "text": text,
            "position": position,
            "bg_color": BRAND_BLACK,
            "text_color": BRAND_WHITE,
        })

    def add_map_scene(
        self, location: str, lat: float, lon: float, duration: float = 6.0
    ) -> None:
        """Add a map visualization scene."""
        self.add_scene("map", duration, {
            "location": location,
            "lat": lat,
            "lon": lon,
        })

    def add_document_scene(
        self, document_title: str, excerpt: str, duration: float = 8.0
    ) -> None:
        """Add a document/declassified file scene."""
        self.add_scene("document", duration, {
            "document_title": document_title,
            "excerpt": excerpt,
            "style": "classified",
        })

    def build_scene_clips(self) -> list[Any]:
        """Build MoviePy clips for each scene.

        Returns:
            List of MoviePy clip objects.
        """
        try:
            from moviepy.editor import (
                ColorClip,
                TextClip,
                CompositeVideoClip,
            )
        except ImportError:
            self.log.error("video.moviepy_not_installed")
            return []

        clips = []

        for scene in self.scenes:
            if scene["type"] == "title_card":
                bg = ColorClip(
                    size=(self.width, self.height),
                    color=scene["content"]["bg_color"],
                    duration=scene["duration"],
                )
                title_clip = TextClip(
                    scene["content"]["title"],
                    fontsize=72 if self.format == "standard" else 56,
                    color="white",
                    font="JetBrains-Mono-Bold",
                    size=(self.width - 200, None),
                    method="caption",
                ).set_position("center").set_duration(scene["duration"])

                clip = CompositeVideoClip([bg, title_clip])
                clips.append(clip)

            elif scene["type"] == "text_overlay":
                bg = ColorClip(
                    size=(self.width, self.height),
                    color=scene["content"]["bg_color"],
                    duration=scene["duration"],
                )
                text_clip = TextClip(
                    scene["content"]["text"],
                    fontsize=48 if self.format == "standard" else 36,
                    color="white",
                    font="Inter",
                    size=(self.width - 200, None),
                    method="caption",
                ).set_position("center").set_duration(scene["duration"])

                clip = CompositeVideoClip([bg, text_clip])
                clips.append(clip)

            else:
                # Fallback: dark frame with label
                bg = ColorClip(
                    size=(self.width, self.height),
                    color=BRAND_BLACK,
                    duration=scene["duration"],
                )
                clips.append(bg)

        return clips

    def assemble(self) -> Path | None:
        """Assemble the final video from all scenes and narration.

        Returns:
            Path to the output video file, or None on error.
        """
        try:
            from moviepy.editor import (
                AudioFileClip,
                concatenate_videoclips,
                CompositeVideoClip,
            )
        except ImportError:
            self.log.error("video.moviepy_not_installed")
            return None

        if not self.scenes:
            self.log.error("video.no_scenes")
            return None

        self.log.info(
            "video.assembling",
            scene_count=len(self.scenes),
            has_narration=self.narration_path is not None,
        )

        try:
            clips = self.build_scene_clips()
            if not clips:
                return None

            video = concatenate_videoclips(clips, method="compose")

            # Add narration audio if available
            if self.narration_path and self.narration_path.exists():
                audio = AudioFileClip(str(self.narration_path))
                video = video.set_audio(audio)

            # Output path
            output_filename = f"dead_drop_{self.title[:30].replace(' ', '_').lower()}.mp4"
            output_path = self.output_dir / output_filename

            video.write_videofile(
                str(output_path),
                fps=VIDEO_FPS,
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                threads=4,
            )

            self.log.info(
                "video.assembled",
                output_path=str(output_path),
                duration=video.duration,
            )

            return output_path

        except Exception as exc:
            self.log.exception("video.assemble_error", error=str(exc))
            return None

    def get_project_summary(self) -> dict[str, Any]:
        """Get a summary of the video project."""
        total_duration = sum(s["duration"] for s in self.scenes)
        return {
            "title": self.title,
            "format": self.format,
            "resolution": f"{self.width}x{self.height}",
            "scene_count": len(self.scenes),
            "total_duration_seconds": total_duration,
            "has_narration": self.narration_path is not None,
        }


def create_standard_episode(
    title: str,
    script_text: str,
    narration_path: Path | None,
    output_dir: Path,
) -> VideoProject:
    """Create a standard Dead Drop video episode from a script.

    Parses [B-ROLL], [MAP], [DOCUMENT] cues from the script
    and builds scenes automatically.

    Args:
        title: Episode title.
        script_text: Full video script with visual cues.
        narration_path: Path to narration audio file.
        output_dir: Directory for output video.

    Returns:
        Configured VideoProject ready to assemble.
    """
    project = VideoProject(title=title, output_dir=output_dir)

    if narration_path:
        project.set_narration(narration_path)

    # Add branded intro
    project.add_title_card(
        title="DEAD DROP",
        subtitle=title,
        duration=5.0,
    )

    # Parse script for visual cues and create scenes
    import re
    lines = script_text.split("\n")
    current_text = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        broll_match = re.match(r"\[B-ROLL:\s*(.+?)\]", line)
        map_match = re.match(r"\[MAP:\s*(.+?)\]", line)
        doc_match = re.match(r"\[DOCUMENT:\s*(.+?)\]", line)

        if broll_match:
            if current_text:
                project.add_text_overlay(current_text, duration=8.0)
                current_text = ""
            project.add_scene("b_roll", 6.0, {"description": broll_match.group(1)})
        elif map_match:
            if current_text:
                project.add_text_overlay(current_text, duration=8.0)
                current_text = ""
            project.add_map_scene(map_match.group(1), 0, 0, duration=6.0)
        elif doc_match:
            if current_text:
                project.add_text_overlay(current_text, duration=8.0)
                current_text = ""
            project.add_document_scene(doc_match.group(1), "", duration=8.0)
        else:
            current_text += " " + line if current_text else line

    if current_text:
        project.add_text_overlay(current_text, duration=8.0)

    # Add branded outro
    project.add_title_card(
        title="DEAD DROP",
        subtitle="Subscribe at dead-drop.co",
        duration=5.0,
    )

    return project

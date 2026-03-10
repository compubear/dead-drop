"""Dead Drop Pipeline — Thumbnail generator.

Creates branded YouTube thumbnails for Dead Drop episodes.
Uses Pillow for image generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# Thumbnail dimensions
THUMB_WIDTH = 1280
THUMB_HEIGHT = 720

# Brand colors
BG_COLOR = (15, 15, 15)
RED_ACCENT = (220, 38, 38)
WHITE = (245, 245, 245)
STEEL = (148, 163, 184)


def generate_thumbnail(
    title: str,
    pillar: str,
    output_path: Path,
    subtitle: str = "",
) -> Path | None:
    """Generate a branded Dead Drop thumbnail.

    Args:
        title: Episode title (main text).
        pillar: Content pillar (used for accent color/badge).
        output_path: Path to save the thumbnail.
        subtitle: Optional subtitle text.

    Returns:
        Path to the generated thumbnail, or None on error.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.error("thumbnail.pillow_not_installed")
        return None

    log = logger.bind(title=title[:60])
    log.info("thumbnail.generating")

    try:
        # Create base image
        img = Image.new("RGB", (THUMB_WIDTH, THUMB_HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Try to load fonts, fall back to defaults
        try:
            title_font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 64)
            subtitle_font = ImageFont.truetype("DejaVuSans.ttf", 32)
            badge_font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 24)
        except (IOError, OSError):
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            badge_font = ImageFont.load_default()

        # Red accent bar at top
        draw.rectangle([(0, 0), (THUMB_WIDTH, 8)], fill=RED_ACCENT)

        # "DEAD DROP" watermark
        draw.text(
            (60, 40),
            "DEAD DROP",
            fill=RED_ACCENT,
            font=badge_font,
        )

        # Pillar badge
        pillar_colors = {
            "intelligence": (37, 99, 235),
            "conflicts": (220, 38, 38),
            "ai": (139, 92, 246),
            "cyber": (16, 185, 129),
            "historical": (217, 119, 6),
        }
        badge_color = pillar_colors.get(pillar, STEEL)
        badge_text = pillar.upper()
        badge_x = THUMB_WIDTH - 250
        draw.rectangle(
            [(badge_x, 35), (badge_x + 180, 65)],
            fill=badge_color,
        )
        draw.text(
            (badge_x + 10, 40),
            badge_text,
            fill=WHITE,
            font=badge_font,
        )

        # Main title (word-wrapped)
        max_chars_per_line = 25
        words = title.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) > max_chars_per_line:
                lines.append(current_line.strip())
                current_line = word
            else:
                current_line += " " + word
        if current_line:
            lines.append(current_line.strip())

        y_offset = THUMB_HEIGHT // 2 - (len(lines) * 80) // 2
        for line in lines[:3]:  # Max 3 lines
            draw.text(
                (60, y_offset),
                line.upper(),
                fill=WHITE,
                font=title_font,
            )
            y_offset += 80

        # Subtitle
        if subtitle:
            draw.text(
                (60, y_offset + 20),
                subtitle,
                fill=STEEL,
                font=subtitle_font,
            )

        # Bottom red accent bar
        draw.rectangle(
            [(0, THUMB_HEIGHT - 8), (THUMB_WIDTH, THUMB_HEIGHT)],
            fill=RED_ACCENT,
        )

        # Grid overlay effect (scan lines)
        for y in range(0, THUMB_HEIGHT, 4):
            draw.line(
                [(0, y), (THUMB_WIDTH, y)],
                fill=(255, 255, 255),
                width=1,
            )
            # Make scan lines very subtle
            img.paste(
                Image.new("RGB", (THUMB_WIDTH, 1), BG_COLOR),
                (0, y),
                Image.new("L", (THUMB_WIDTH, 1), 10),  # Very low alpha
            )

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path), quality=95)

        log.info("thumbnail.generated", output_path=str(output_path))
        return output_path

    except Exception as exc:
        log.exception("thumbnail.error", error=str(exc))
        return None

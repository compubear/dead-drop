"""Dead Drop — Sprint 6 tests: Video production pipeline."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from video.narration import NarrationGenerator
from video.assembler import (
    VideoProject,
    create_standard_episode,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    SHORTS_WIDTH,
    SHORTS_HEIGHT,
)
from video.thumbnail import THUMB_WIDTH, THUMB_HEIGHT
from video.youtube_upload import YouTubeUploader, DEFAULT_TAGS


class TestNarration:
    """Test ElevenLabs narration generator."""

    def test_no_api_key(self):
        with patch("video.narration.settings") as mock_s:
            mock_s.ELEVENLABS_API_KEY = ""
            gen = NarrationGenerator()
            result = gen.generate_narration("Hello", Path("/tmp/test.mp3"))
            assert result is None

    def test_duration_estimate(self):
        with patch("video.narration.settings") as mock_s:
            mock_s.ELEVENLABS_API_KEY = "test"
            gen = NarrationGenerator()
            # 150 words = 1 minute = 60 seconds
            text = " ".join(["word"] * 150)
            duration = gen.estimate_duration(text)
            assert abs(duration - 60.0) < 0.1

    def test_voice_list_no_key(self):
        with patch("video.narration.settings") as mock_s:
            mock_s.ELEVENLABS_API_KEY = ""
            gen = NarrationGenerator()
            assert gen.get_available_voices() == []


class TestVideoAssembler:
    """Test video assembly."""

    def test_standard_project_dimensions(self):
        project = VideoProject("Test", Path("/tmp"), format="standard")
        assert project.width == VIDEO_WIDTH
        assert project.height == VIDEO_HEIGHT

    def test_shorts_project_dimensions(self):
        project = VideoProject("Test", Path("/tmp"), format="shorts")
        assert project.width == SHORTS_WIDTH
        assert project.height == SHORTS_HEIGHT

    def test_add_scenes(self):
        project = VideoProject("Test", Path("/tmp"))
        project.add_title_card("Title", "Subtitle", 5.0)
        project.add_text_overlay("Key point", 8.0)
        project.add_map_scene("Moscow", 55.75, 37.62, 6.0)
        project.add_document_scene("CIA Report", "Excerpt", 8.0)
        assert len(project.scenes) == 4

    def test_project_summary(self):
        project = VideoProject("Test Episode", Path("/tmp"))
        project.add_title_card("Title", duration=5.0)
        project.add_text_overlay("Text", duration=10.0)
        summary = project.get_project_summary()
        assert summary["title"] == "Test Episode"
        assert summary["scene_count"] == 2
        assert summary["total_duration_seconds"] == 15.0
        assert summary["has_narration"] is False

    def test_create_standard_episode_parses_cues(self):
        script = """Opening narration text.

[B-ROLL: Satellite imagery of military base]

More narration here.

[MAP: Eastern Ukraine]

[DOCUMENT: Declassified CIA memo 1973]

Closing thoughts."""

        project = create_standard_episode(
            title="Test Episode",
            script_text=script,
            narration_path=None,
            output_dir=Path("/tmp/test_video"),
        )

        # Should have: intro title + text + b_roll + text + map + document + text + outro title
        assert len(project.scenes) >= 6
        scene_types = [s["type"] for s in project.scenes]
        assert "title_card" in scene_types
        assert "b_roll" in scene_types
        assert "map" in scene_types
        assert "document" in scene_types


class TestYouTubeUploader:
    """Test YouTube uploader."""

    def test_upload_not_configured(self):
        with patch("video.youtube_upload.settings") as mock_s:
            mock_s.YOUTUBE_API_KEY = ""
            uploader = YouTubeUploader()
            assert uploader.api_key == ""

    def test_video_not_found(self):
        with patch("video.youtube_upload.settings") as mock_s:
            mock_s.YOUTUBE_API_KEY = "test"
            uploader = YouTubeUploader()
            result = uploader.upload_video(
                Path("/nonexistent/video.mp4"),
                "Title",
                "Description",
            )
            assert result is None

    def test_build_description(self):
        with patch("video.youtube_upload.settings") as mock_s:
            mock_s.YOUTUBE_API_KEY = "test"
            uploader = YouTubeUploader()
            desc = uploader.build_description(
                "Test Story",
                "A brief summary",
                sources=["https://example.com"],
            )
            assert "DEAD DROP" in desc
            assert "Test Story" in desc
            assert "dead-drop.co" in desc
            assert "https://example.com" in desc
            assert "5-point verification" in desc

    def test_default_tags(self):
        assert "dead drop" in DEFAULT_TAGS
        assert "intelligence" in DEFAULT_TAGS
        assert len(DEFAULT_TAGS) > 5

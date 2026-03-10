"""Dead Drop — Sprint 4 tests: Content generation engine."""

import pytest
from unittest.mock import patch, MagicMock

from pipeline.content_gen.generator import (
    generate_content,
    generate_all_formats,
    PROMPT_MAP,
    NEWSLETTER_PROMPT,
    TWITTER_THREAD_PROMPT,
    VIDEO_SCRIPT_PROMPT,
    REDDIT_POST_PROMPT,
    TELEGRAM_PROMPT,
    SHORTS_SCRIPT_PROMPT,
)


class TestPromptTemplates:
    """Test content generation prompt templates."""

    def test_all_content_types_have_prompts(self):
        """Test that all content types have associated prompts."""
        expected_types = [
            "newsletter", "twitter_thread", "video_script",
            "reddit_post", "telegram", "shorts_script",
        ]
        for ct in expected_types:
            assert ct in PROMPT_MAP, f"Missing prompt for {ct}"

    def test_newsletter_prompt_has_voice_rules(self):
        """Test newsletter prompt includes Dead Drop voice rules."""
        assert "authoritative" in NEWSLETTER_PROMPT.lower()
        assert "conspiratorial" in NEWSLETTER_PROMPT.lower()

    def test_twitter_prompt_has_character_limit(self):
        """Test Twitter prompt mentions character limits."""
        assert "280" in TWITTER_THREAD_PROMPT

    def test_video_prompt_has_structure(self):
        """Test video prompt includes script structure."""
        assert "COLD OPEN" in VIDEO_SCRIPT_PROMPT
        assert "B-ROLL" in VIDEO_SCRIPT_PROMPT
        assert "MAP" in VIDEO_SCRIPT_PROMPT

    def test_shorts_prompt_is_concise(self):
        """Test Shorts prompt enforces brevity."""
        assert "150 words" in SHORTS_SCRIPT_PROMPT
        assert "30-60 seconds" in SHORTS_SCRIPT_PROMPT

    def test_telegram_prompt_has_length_limit(self):
        """Test Telegram prompt has character limit."""
        assert "1000 characters" in TELEGRAM_PROMPT


class TestContentGeneration:
    """Test content generation functionality."""

    def test_generate_content_no_api_key(self):
        """Test that generation returns None without API key."""
        with patch("pipeline.content_gen.generator.settings") as mock_s:
            mock_s.CLAUDE_API_KEY = ""
            result = generate_content(
                {"title": "Test", "content": "Content"},
                "newsletter",
            )
            assert result is None

    @patch("pipeline.content_gen.generator.anthropic.Anthropic")
    def test_generate_content_success(self, mock_anthropic_cls):
        """Test successful content generation."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "# Test Newsletter\n\nGenerated content here."
        mock_client.messages.create.return_value = mock_response

        with patch("pipeline.content_gen.generator.settings") as mock_s:
            mock_s.CLAUDE_API_KEY = "test-key"
            result = generate_content(
                {"title": "Test Story", "content": "Story content", "pillar": "ai"},
                "newsletter",
            )

        assert result is not None
        assert result["content_type"] == "newsletter"
        assert "content" in result
        assert "generated_at" in result
        assert result["word_count"] > 0

    def test_generate_content_unknown_type(self):
        """Test that unknown content type returns None."""
        with patch("pipeline.content_gen.generator.settings") as mock_s:
            mock_s.CLAUDE_API_KEY = "test-key"
            result = generate_content(
                {"title": "Test"},
                "invalid_type",  # type: ignore
            )
            assert result is None


class TestBatchGeneration:
    """Test batch content generation."""

    @patch("pipeline.content_gen.generator.generate_content")
    def test_generate_all_formats_default(self, mock_gen):
        """Test generating all default formats."""
        mock_gen.return_value = {"content": "test", "content_type": "newsletter"}

        results = generate_all_formats({"title": "Test"})

        assert len(results) == 4  # Default: newsletter, twitter, video, telegram
        assert mock_gen.call_count == 4

    @patch("pipeline.content_gen.generator.generate_content")
    def test_generate_specific_formats(self, mock_gen):
        """Test generating specific formats only."""
        mock_gen.return_value = {"content": "test"}

        results = generate_all_formats(
            {"title": "Test"},
            formats=["newsletter", "telegram"],
        )

        assert len(results) == 2
        assert "newsletter" in results
        assert "telegram" in results

    @patch("pipeline.content_gen.generator.generate_content")
    def test_generate_handles_failures(self, mock_gen):
        """Test that batch handles individual failures gracefully."""
        mock_gen.side_effect = [
            {"content": "ok"},
            None,  # failure
            {"content": "also ok"},
        ]

        results = generate_all_formats(
            {"title": "Test"},
            formats=["newsletter", "twitter_thread", "telegram"],
        )

        assert results["newsletter"] is not None
        assert results["twitter_thread"] is None
        assert results["telegram"] is not None

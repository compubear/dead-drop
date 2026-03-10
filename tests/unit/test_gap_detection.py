"""Dead Drop — Sprint 2 tests: Gap Detection Engine."""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from pipeline.gap_detection.scorer import (
    build_scoring_prompt,
    score_item,
    score_items_batch,
    select_top_stories,
    SCORING_SYSTEM_PROMPT,
)


class TestScoringPrompt:
    """Test scoring prompt construction."""

    def test_build_prompt_includes_title(self):
        """Test that prompt includes the item title."""
        item = {
            "title": "CIA Releases New Documents",
            "content": "Some content",
            "url": "https://example.com",
            "metadata": {"pillar": "intelligence", "source_name": "CIA FOIA"},
        }
        prompt = build_scoring_prompt(item)
        assert "CIA Releases New Documents" in prompt

    def test_build_prompt_includes_source(self):
        """Test that prompt includes source name."""
        item = {
            "title": "Test",
            "content": "Content",
            "url": "https://example.com",
            "metadata": {"source_name": "The Black Vault", "pillar": "intelligence"},
        }
        prompt = build_scoring_prompt(item)
        assert "The Black Vault" in prompt

    def test_build_prompt_truncates_long_content(self):
        """Test that very long content is truncated."""
        item = {
            "title": "Test",
            "content": "x" * 10000,
            "url": "https://example.com",
            "metadata": {},
        }
        prompt = build_scoring_prompt(item)
        # Content should be truncated to 3000 chars
        assert len(prompt) < 4000

    def test_build_prompt_handles_missing_metadata(self):
        """Test prompt with no metadata."""
        item = {"title": "Test", "content": "Content"}
        prompt = build_scoring_prompt(item)
        assert "unknown" in prompt

    def test_system_prompt_contains_key_instructions(self):
        """Test that system prompt has essential instructions."""
        assert "SIGNIFICANCE" in SCORING_SYSTEM_PROMPT
        assert "COVERAGE" in SCORING_SYSTEM_PROMPT
        assert "JSON" in SCORING_SYSTEM_PROMPT
        assert "Dead Drop" in SCORING_SYSTEM_PROMPT


class TestScoreItem:
    """Test individual item scoring."""

    def test_score_item_no_api_key(self):
        """Test that scoring returns None without API key."""
        with patch("pipeline.gap_detection.scorer.settings") as mock_settings:
            mock_settings.CLAUDE_API_KEY = ""
            result = score_item({"title": "Test", "content": "Content"})
            assert result is None

    @patch("pipeline.gap_detection.scorer.anthropic.Anthropic")
    def test_score_item_success(self, mock_anthropic_class):
        """Test successful scoring with mocked Claude."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "significance_score": 8.5,
            "coverage_score": 2.0,
            "reasoning": "Important story, low coverage",
            "suggested_title": "Hidden Intelligence Report",
            "pillar": "intelligence",
            "key_entities": ["CIA", "NSA"],
            "verification_needed": "Check primary source",
        })
        mock_client.messages.create.return_value = mock_response

        with patch("pipeline.gap_detection.scorer.settings") as mock_settings:
            mock_settings.CLAUDE_API_KEY = "test-key"

            result = score_item({"title": "Test Story", "content": "Content", "metadata": {}})

            assert result is not None
            assert result["significance_score"] == 8.5
            assert result["coverage_score"] == 2.0
            assert result["gap_score"] == 6.5
            assert "scored_at" in result

    @patch("pipeline.gap_detection.scorer.anthropic.Anthropic")
    def test_score_item_invalid_json(self, mock_anthropic_class):
        """Test handling of invalid JSON response."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "not valid json"
        mock_client.messages.create.return_value = mock_response

        with patch("pipeline.gap_detection.scorer.settings") as mock_settings:
            mock_settings.CLAUDE_API_KEY = "test-key"
            result = score_item({"title": "Test", "content": "Content", "metadata": {}})
            assert result is None


class TestStorySelection:
    """Test story selection logic."""

    def _make_scored_item(self, pillar: str, gap_score: float) -> dict:
        return {
            "title": f"Story about {pillar}",
            "scoring": {
                "pillar": pillar,
                "gap_score": gap_score,
                "significance_score": gap_score + 3,
                "coverage_score": 3,
            },
        }

    def test_select_top_stories_basic(self):
        """Test basic top story selection."""
        items = [
            self._make_scored_item("intelligence", 7.0),
            self._make_scored_item("cyber", 6.0),
            self._make_scored_item("ai", 5.0),
        ]
        selected = select_top_stories(items, max_stories=2, ensure_pillar_diversity=False)
        assert len(selected) == 2
        assert selected[0]["scoring"]["gap_score"] == 7.0

    def test_select_top_stories_with_diversity(self):
        """Test that pillar diversity is enforced."""
        items = [
            self._make_scored_item("intelligence", 9.0),
            self._make_scored_item("intelligence", 8.0),
            self._make_scored_item("intelligence", 7.0),
            self._make_scored_item("cyber", 6.0),
            self._make_scored_item("ai", 5.0),
        ]
        selected = select_top_stories(items, max_stories=3, ensure_pillar_diversity=True)
        pillars = {s["scoring"]["pillar"] for s in selected}
        # Should include at least 3 different pillars
        assert len(pillars) == 3

    def test_select_top_stories_empty(self):
        """Test selection with empty list."""
        selected = select_top_stories([], max_stories=5)
        assert selected == []

    def test_select_top_stories_fewer_than_max(self):
        """Test selection when fewer items than max."""
        items = [self._make_scored_item("ai", 7.0)]
        selected = select_top_stories(items, max_stories=5)
        assert len(selected) == 1


class TestBatchScoring:
    """Test batch scoring functionality."""

    def test_batch_scoring_filters_by_threshold(self):
        """Test that batch scoring filters below threshold."""
        with patch("pipeline.gap_detection.scorer.score_item") as mock_score:
            mock_score.side_effect = [
                {"gap_score": 7.0, "significance_score": 9, "coverage_score": 2},
                {"gap_score": 1.0, "significance_score": 4, "coverage_score": 3},
                {"gap_score": 5.0, "significance_score": 8, "coverage_score": 3},
            ]

            items = [
                {"title": "A", "content": "a"},
                {"title": "B", "content": "b"},
                {"title": "C", "content": "c"},
            ]

            results = score_items_batch(items, min_gap_score=3.0)
            assert len(results) == 2  # Only gap scores >= 3.0

    def test_batch_scoring_sorts_by_gap(self):
        """Test that results are sorted by gap score descending."""
        with patch("pipeline.gap_detection.scorer.score_item") as mock_score:
            mock_score.side_effect = [
                {"gap_score": 5.0},
                {"gap_score": 8.0},
                {"gap_score": 3.0},
            ]

            items = [{"title": f"Item {i}", "content": "c"} for i in range(3)]
            results = score_items_batch(items, min_gap_score=0)

            gaps = [r["scoring"]["gap_score"] for r in results]
            assert gaps == [8.0, 5.0, 3.0]

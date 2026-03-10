"""Dead Drop Pipeline — Gap Detection Scoring Engine.

The core scoring engine that uses Claude to evaluate each item
on two dimensions: Significance (1-10) and Coverage (1-10).
The GAP SCORE = Significance - Coverage.

High gap score = important story with low media coverage = Dead Drop material.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import anthropic
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

# Claude model for scoring
SCORING_MODEL = "claude-sonnet-4-20250514"

# System prompt for gap detection scoring
SCORING_SYSTEM_PROMPT = """You are an intelligence analyst working for Dead Drop, a media platform focused on underreported stories in intelligence, geopolitics, conflicts, AI/technology, cybersecurity, and historical revelations.

Your task is to evaluate each news item on TWO dimensions:

1. **SIGNIFICANCE SCORE (1-10)**: How important is this story for understanding world events?
   - 1-3: Minor, routine, or highly localized
   - 4-6: Moderately important, some broader implications
   - 7-8: Significant, affects multiple countries or major policy areas
   - 9-10: Critical, potentially history-altering or paradigm-shifting

2. **COVERAGE SCORE (1-10)**: How much media attention has this story received?
   - 1-3: Almost no coverage, buried in reports/documents, only specialists know
   - 4-6: Some coverage but limited to niche outlets
   - 7-8: Moderate coverage in mainstream media
   - 9-10: Widely covered, trending, front-page news

The GAP SCORE is calculated as: Significance - Coverage.
A HIGH gap score means: important story + low coverage → perfect Dead Drop material.

You MUST be rigorous, skeptical, and factual. Do NOT sensationalize.
You MUST cite specific reasons for your scores.

Respond ONLY with valid JSON in this exact format:
{
    "significance_score": <float 1.0-10.0>,
    "coverage_score": <float 1.0-10.0>,
    "reasoning": "<2-3 sentences explaining your scores>",
    "suggested_title": "<a compelling, factual title for this story>",
    "pillar": "<intelligence|conflicts|ai|cyber|historical>",
    "key_entities": ["<entity1>", "<entity2>"],
    "verification_needed": "<what specific claims need verification>"
}"""


def build_scoring_prompt(item: dict[str, Any]) -> str:
    """Build the user prompt for scoring a single item.

    Args:
        item: Raw item dict with title, content, url, metadata.

    Returns:
        Formatted prompt string.
    """
    pillar = item.get("metadata", {}).get("pillar", "unknown")
    source_name = item.get("metadata", {}).get("source_name", "unknown")

    return f"""Evaluate this item for Dead Drop publication:

**Source:** {source_name}
**Pillar:** {pillar}
**Title:** {item.get('title', 'No title')}
**URL:** {item.get('url', 'No URL')}
**Content:**
{item.get('content', 'No content available')[:3000]}

Score this item on Significance (1-10) and Coverage (1-10).
Respond with JSON only."""


def score_item(item: dict[str, Any]) -> dict[str, Any] | None:
    """Score a single item using Claude.

    Args:
        item: Raw item dict from the source monitoring pipeline.

    Returns:
        Scoring result dict, or None on error.
    """
    log = logger.bind(title=item.get("title", "unknown")[:80])

    if not settings.CLAUDE_API_KEY:
        log.warning("gap_detection.no_api_key")
        return None

    try:
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

        message = client.messages.create(
            model=SCORING_MODEL,
            max_tokens=500,
            system=SCORING_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": build_scoring_prompt(item),
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text.strip()

        # Handle potential markdown code block wrapping
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        result = json.loads(response_text)

        # Validate scores
        sig = float(result.get("significance_score", 0))
        cov = float(result.get("coverage_score", 0))

        if not (1 <= sig <= 10) or not (1 <= cov <= 10):
            log.warning("gap_detection.invalid_scores", sig=sig, cov=cov)
            return None

        result["gap_score"] = round(sig - cov, 1)
        result["scored_at"] = datetime.now(timezone.utc).isoformat()
        result["model"] = SCORING_MODEL

        log.info(
            "gap_detection.scored",
            significance=sig,
            coverage=cov,
            gap=result["gap_score"],
        )

        return result

    except json.JSONDecodeError as exc:
        log.error("gap_detection.json_parse_error", error=str(exc))
        return None
    except anthropic.APIError as exc:
        log.error("gap_detection.api_error", error=str(exc))
        return None
    except Exception as exc:
        log.exception("gap_detection.error", error=str(exc))
        return None


def score_items_batch(
    items: list[dict[str, Any]],
    min_gap_score: float = 3.0,
) -> list[dict[str, Any]]:
    """Score a batch of items and filter by minimum gap score.

    Args:
        items: List of raw item dicts.
        min_gap_score: Minimum gap score to include in results.

    Returns:
        List of scored items meeting the threshold, sorted by gap score descending.
    """
    scored = []

    for item in items:
        result = score_item(item)
        if result and result.get("gap_score", 0) >= min_gap_score:
            scored.append({
                **item,
                "scoring": result,
            })

    # Sort by gap score descending
    scored.sort(key=lambda x: x["scoring"]["gap_score"], reverse=True)

    logger.info(
        "gap_detection.batch_complete",
        total_items=len(items),
        scored=len(scored),
        above_threshold=len(scored),
        min_gap_score=min_gap_score,
    )

    return scored


def select_top_stories(
    scored_items: list[dict[str, Any]],
    max_stories: int = 5,
    ensure_pillar_diversity: bool = True,
) -> list[dict[str, Any]]:
    """Select top stories from scored items.

    Optionally ensures pillar diversity so we don't publish
    5 cyber stories and ignore everything else.

    Args:
        scored_items: Scored and sorted items.
        max_stories: Maximum number to select.
        ensure_pillar_diversity: If True, try to include different pillars.

    Returns:
        Selected top stories.
    """
    if not ensure_pillar_diversity:
        return scored_items[:max_stories]

    selected: list[dict[str, Any]] = []
    pillars_used: set[str] = set()

    # First pass: one story per pillar
    for item in scored_items:
        pillar = item.get("scoring", {}).get("pillar", "unknown")
        if pillar not in pillars_used:
            selected.append(item)
            pillars_used.add(pillar)
            if len(selected) >= max_stories:
                break

    # Second pass: fill remaining slots with highest gap scores
    if len(selected) < max_stories:
        for item in scored_items:
            if item not in selected:
                selected.append(item)
                if len(selected) >= max_stories:
                    break

    logger.info(
        "gap_detection.stories_selected",
        count=len(selected),
        pillars=list(pillars_used),
    )

    return selected

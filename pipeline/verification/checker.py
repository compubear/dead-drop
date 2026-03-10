"""Dead Drop Pipeline — Content verification module.

Implements the 5-point verification protocol from the PRD:
1. Primary Source Verification
2. Claim Cross-Referencing
3. Uncertainty Labeling
4. Bias Check
5. Human Review Flag
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import anthropic
import structlog

from pipeline.config import settings
from pipeline.db.connection import get_connection

logger = structlog.get_logger()

VERIFICATION_MODEL = "claude-sonnet-4-20250514"

VERIFICATION_PROMPT = """You are a fact-checker for Dead Drop, an intelligence and geopolitics media platform.

Your job is to verify a story draft using our 5-point verification protocol.

For each point, assess:

1. **PRIMARY SOURCE VERIFICATION**: Can this story be traced to a primary source (official document, court filing, government database, FOIA release, academic paper)?
   - Identify the primary source
   - Rate confidence: HIGH / MEDIUM / LOW / UNVERIFIABLE

2. **CLAIM CROSS-REFERENCE**: Can the key claims be independently verified through at least one other source?
   - List which claims are verifiable and which are not
   - Note any contradictory information found

3. **UNCERTAINTY LABELING**: Are there areas where facts are uncertain?
   - List specific claims that should be labeled with uncertainty language ("allegedly", "according to", "unconfirmed reports suggest")
   - Identify any speculation that should be removed

4. **BIAS CHECK**: Does the story contain ideological bias, sensationalism, or conspiratorial framing?
   - Rate bias level: NONE / MINOR / MODERATE / SIGNIFICANT
   - Note specific passages that need toning down

5. **HUMAN REVIEW FLAG**: Does this story require human editorial review before publication?
   - YES/NO with reasoning

Respond with JSON:
{
    "primary_source": {
        "verified": true/false,
        "source_url": "url or description",
        "confidence": "HIGH/MEDIUM/LOW/UNVERIFIABLE"
    },
    "cross_reference": {
        "verified": true/false,
        "notes": "details",
        "verifiable_claims": ["claim1", "claim2"],
        "unverifiable_claims": ["claim3"]
    },
    "uncertainty": {
        "labeled": true/false,
        "uncertain_claims": ["claim that needs uncertainty language"],
        "speculation_to_remove": ["speculation to cut"]
    },
    "bias_check": {
        "passed": true/false,
        "level": "NONE/MINOR/MODERATE/SIGNIFICANT",
        "notes": "details"
    },
    "human_review_required": true/false,
    "human_review_reason": "why or why not",
    "overall_verdict": "PUBLISH/REVISE/REJECT",
    "revision_notes": "specific changes needed if REVISE"
}"""


def verify_story(
    title: str,
    content: str,
    source_url: str = "",
    pillar: str = "",
) -> dict[str, Any] | None:
    """Run the 5-point verification protocol on a story.

    Args:
        title: Story title.
        content: Story content/draft.
        source_url: Primary source URL.
        pillar: Content pillar.

    Returns:
        Verification result dict, or None on error.
    """
    log = logger.bind(title=title[:80])

    if not settings.CLAUDE_API_KEY:
        log.warning("verification.no_api_key")
        return None

    try:
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

        user_prompt = f"""Verify this story for publication:

**Title:** {title}
**Pillar:** {pillar}
**Source URL:** {source_url}
**Content:**
{content[:4000]}

Run the full 5-point verification protocol. Respond with JSON only."""

        message = client.messages.create(
            model=VERIFICATION_MODEL,
            max_tokens=1000,
            system=VERIFICATION_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        result = json.loads(response_text)

        log.info(
            "verification.complete",
            verdict=result.get("overall_verdict"),
            human_review=result.get("human_review_required"),
        )

        return result

    except Exception as exc:
        log.exception("verification.error", error=str(exc))
        return None


def store_verification(story_id: int, result: dict[str, Any]) -> int | None:
    """Persist verification results to the database.

    Args:
        story_id: ID of the story being verified.
        result: Verification result dict from verify_story().

    Returns:
        Verification record ID, or None on error.
    """
    conn = get_connection()

    try:
        primary = result.get("primary_source", {})
        cross_ref = result.get("cross_reference", {})
        uncertainty = result.get("uncertainty", {})
        bias = result.get("bias_check", {})

        row = conn.execute(
            """
            INSERT INTO verifications (
                story_id,
                primary_source_verified, primary_source_url,
                claims_cross_referenced, cross_reference_notes,
                uncertainty_labeled,
                bias_check_passed, bias_check_notes,
                human_approved, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            [
                story_id,
                primary.get("verified", False),
                primary.get("source_url", ""),
                cross_ref.get("verified", False),
                cross_ref.get("notes", ""),
                uncertainty.get("labeled", False),
                bias.get("passed", False),
                bias.get("notes", ""),
                False,  # human_approved starts as False
                result.get("revision_notes", ""),
            ],
        ).fetchone()

        conn.commit()

        if row:
            logger.info("verification.stored", verification_id=row[0], story_id=story_id)
            return row[0]
        return None

    except Exception as exc:
        conn.rollback()
        logger.error("verification.store_error", error=str(exc))
        raise

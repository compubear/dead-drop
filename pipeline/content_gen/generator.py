"""Dead Drop Pipeline — Content generation engine.

Uses Claude to generate multi-format content from scored/verified stories.
Supports: newsletters, Twitter threads, video scripts, Reddit posts,
Telegram posts, and YouTube Shorts scripts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal

import anthropic
import structlog

from pipeline.config import settings

logger = structlog.get_logger()

ContentType = Literal[
    "newsletter", "twitter_thread", "video_script",
    "reddit_post", "telegram", "shorts_script",
]

CONTENT_MODEL = "claude-sonnet-4-20250514"

# === PROMPT TEMPLATES ===

NEWSLETTER_PROMPT = """You are the editor of Dead Drop, an intelligence and geopolitics newsletter.

Write a newsletter section for this story. Follow this structure:
1. **HEADLINE** — Punchy, factual, no clickbait
2. **HOOK** — 1-2 sentences that make the reader stop scrolling
3. **BODY** — 3-5 paragraphs of context, analysis, and implications
4. **THE DEAD DROP** — A key insight or takeaway that mainstream media missed
5. **SOURCES** — Links/references

VOICE RULES:
- Authoritative but accessible
- Factual, never conspiratorial
- Dry wit where appropriate
- Write like a senior intelligence analyst briefing someone smart but busy
- ALWAYS attribute claims. Use "according to", "per", "as reported by"
- NEVER use clickbait, sensationalism, or conspiratorial language

FORMAT: Return plain text with markdown formatting."""

TWITTER_THREAD_PROMPT = """You are the Twitter/X voice for Dead Drop (@DeadDropIntel).

Create a Twitter thread (5-8 tweets) about this story.

RULES:
- First tweet must hook — make people stop scrolling
- Keep tweets under 280 characters each
- Use 🧵 on the first tweet
- Include the Dead Drop angle: "why this matters and why no one is talking about it"
- End with a call to action (newsletter link placeholder: [LINK])
- No hashtags except #DeadDrop on the last tweet
- Factual, dry wit, never conspiratorial

FORMAT: Return as JSON array of strings, one per tweet."""

VIDEO_SCRIPT_PROMPT = """You are a scriptwriter for Dead Drop's YouTube documentary channel.

Write a 5-7 minute video script (approx. 800-1000 words narration) for this story.

STRUCTURE:
1. **COLD OPEN** (30 sec): A dramatic factual hook
2. **INTRO** (30 sec): "This is Dead Drop. The stories that fell through the cracks."
3. **CONTEXT** (1-2 min): Background and why this matters
4. **THE STORY** (2-3 min): Core narrative with key details
5. **ANALYSIS** (1 min): What this means and why no one covered it
6. **OUTRO** (30 sec): Subscribe CTA + next episode tease

FORMAT RULES:
- Include [B-ROLL: description] for visual cues
- Include [MAP: location] for geographic context
- Include [DOCUMENT: description] for archival footage cues
- Write for narration — conversational but authoritative
- Each paragraph should be 2-3 sentences for good pacing

Return as plain text with visual cues in [brackets]."""

REDDIT_POST_PROMPT = """Write a Reddit deep-dive post for Dead Drop.

RULES:
- Title should be informative and engaging (not clickbait)
- Start with TL;DR (2-3 sentences)
- Structure with headers (##) for scanability
- Include sources/links in-line
- Be thorough, analytical, and well-sourced
- Write for r/geopolitics or r/IntelligenceHistory audience
- End with discussion questions

FORMAT: Return as markdown text."""

TELEGRAM_PROMPT = """Write a Telegram post for Dead Drop's channel.

RULES:
- Keep under 1000 characters
- Lead with a bold statement
- Use emoji strategically (not excessively)
- Include the key "Dead Drop angle"
- End with a link to the full story: [READ MORE]
- Factual, no speculation

FORMAT: Return as plain text."""

SHORTS_SCRIPT_PROMPT = """Write a YouTube Shorts / TikTok script (30-60 seconds) for Dead Drop.

RULES:
- HOOK in first 3 seconds — must stop the scroll
- Keep the WHOLE script under 150 words
- Punchy, fast-paced, fact-driven
- End with a cliffhanger or call to action
- Include [VISUAL: description] cues
- No filler, every word counts

FORMAT: Return as plain text with visual cues in [brackets]."""

PROMPT_MAP: dict[ContentType, str] = {
    "newsletter": NEWSLETTER_PROMPT,
    "twitter_thread": TWITTER_THREAD_PROMPT,
    "video_script": VIDEO_SCRIPT_PROMPT,
    "reddit_post": REDDIT_POST_PROMPT,
    "telegram": TELEGRAM_PROMPT,
    "shorts_script": SHORTS_SCRIPT_PROMPT,
}


def generate_content(
    story: dict[str, Any],
    content_type: ContentType,
) -> dict[str, Any] | None:
    """Generate content for a specific format.

    Args:
        story: Story dict (from gap detection / user input).
        content_type: Target content format.

    Returns:
        Dict with generated content, or None on error.
    """
    log = logger.bind(
        title=story.get("title", "unknown")[:80],
        content_type=content_type,
    )

    if not settings.CLAUDE_API_KEY:
        log.warning("content_gen.no_api_key")
        return None

    system_prompt = PROMPT_MAP.get(content_type)
    if not system_prompt:
        log.error("content_gen.unknown_type", type=content_type)
        return None

    try:
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

        user_prompt = f"""Generate {content_type.replace('_', ' ')} content for this Dead Drop story:

**Title:** {story.get('title', 'Untitled')}
**Pillar:** {story.get('pillar', 'unknown')}
**Summary:** {story.get('summary', '')}
**Source URL:** {story.get('url', '')}
**Scoring Reasoning:** {story.get('scoring', {}).get('reasoning', '')}

**Full Story Content:**
{story.get('content', 'No content')[:4000]}"""

        message = client.messages.create(
            model=CONTENT_MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        generated = message.content[0].text.strip()

        log.info("content_gen.generated", content_type=content_type, length=len(generated))

        return {
            "content_type": content_type,
            "content": generated,
            "model": CONTENT_MODEL,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "word_count": len(generated.split()),
        }

    except Exception as exc:
        log.exception("content_gen.error", error=str(exc))
        return None


def generate_all_formats(
    story: dict[str, Any],
    formats: list[ContentType] | None = None,
) -> dict[ContentType, dict[str, Any] | None]:
    """Generate content in all requested formats.

    Args:
        story: Story dict.
        formats: List of content types. Defaults to all.

    Returns:
        Dict mapping content type to generated content.
    """
    if formats is None:
        formats = ["newsletter", "twitter_thread", "video_script", "telegram"]

    results: dict[ContentType, dict[str, Any] | None] = {}

    for content_type in formats:
        results[content_type] = generate_content(story, content_type)

    success = sum(1 for v in results.values() if v is not None)
    logger.info(
        "content_gen.batch_complete",
        total=len(formats),
        success=success,
        failed=len(formats) - success,
    )

    return results

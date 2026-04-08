"""Monitor workstream agents.

Shared utilities for monitor agents live here to avoid duplication.
"""

from __future__ import annotations

from core.llm_client import LLMClient
from core.models import Mention, RelevanceResult, SentimentResult


def evaluate_relevance(mention: Mention, llm: LLMClient) -> RelevanceResult:
    """Evaluate whether a mention is relevant to the Mellea Python library.

    Returns a RelevanceResult with is_relevant, relevance_score (1-5), and reason.
    Falls back to not-relevant on any error.
    """
    try:
        result = llm.generate_structured(
            prompt=(
                "Evaluate whether this mention is about the Mellea Python library "
                "(an AI reliability and structured output validation tool). "
                "Return is_relevant (bool), relevance_score (1-5), and reason (short string).\n\n"
                "## Relevance Rules\n"
                "A mention is relevant ONLY if it:\n"
                "- Explicitly mentions 'Mellea' as the Python library (not 'malleable' or similar words)\n"
                "- Relates to AI reliability, safety, trust, structured outputs, or production AI\n"
                "- Contains substantive content (not just a name in a list)\n"
                "- Is from a real user/developer (not automated/bot content)\n\n"
                "EXCLUDE mentions that:\n"
                "- Are about 'malleable' anything (bones, memory, gender, etc.)\n"
                "- Don't explicitly name 'Mellea' as the Python library\n"
                "- Are purely promotional or generic AI discussions without Mellea context\n"
                "- Are about other tools/projects with similar-sounding names\n\n"
                "## Importance Scoring (1-5)\n"
                "5 = High engagement + specific feedback + influential source\n"
                "4 = Specific feedback + moderate engagement OR influential author\n"
                "3 = Specific feedback or usage report\n"
                "2 = General mention with some context\n"
                "1 = Passing mention, minimal context\n\n"
                "If NOT relevant, set is_relevant=false and relevance_score=0.\n\n"
                f"Source: {mention.source}\n"
                f"Title: {mention.title or 'N/A'}\n"
                f"Content: {mention.content[:800]}\n"
                f"Author: {mention.author or 'N/A'}\n"
                f"Score/Engagement: {mention.score or 'N/A'}"
            ),
            output_type=RelevanceResult,
            requirements=[
                "is_relevant must be true only if the mention is about the Mellea Python library",
                "relevance_score must be 0 if not relevant, 1-5 if relevant",
                "reason must be a short explanation (under 100 chars)",
            ],
        )
        return result
    except Exception:
        return RelevanceResult(is_relevant=False, relevance_score=0, reason="evaluation failed")


def classify_sentiment(mention: Mention, llm: LLMClient) -> str:
    """Classify the sentiment of a single mention.

    Returns one of: positive, negative, neutral, mixed.
    Falls back to 'neutral' on any error.
    """
    try:
        result = llm.generate_structured(
            prompt=(
                "Classify the sentiment of this mention of the Mellea library. "
                "Return exactly one of: positive, negative, neutral, mixed.\n\n"
                f"Source: {mention.source}\n"
                f"Title: {mention.title or 'N/A'}\n"
                f"Content: {mention.content[:500]}"
            ),
            output_type=SentimentResult,
            requirements=["Must return exactly one of: positive, negative, neutral, mixed"],
        )
        return result.sentiment
    except Exception:
        return "neutral"
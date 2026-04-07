"""Monitor workstream agents.

Shared utilities for monitor agents live here to avoid duplication.
"""

from __future__ import annotations

from core.llm_client import LLMClient
from core.models import Mention, SentimentResult


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
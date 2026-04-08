from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from agents.monitor import classify_sentiment, evaluate_relevance
from core.briefs import save_brief
from core.config import get_config
from core.llm_client import LLMClient
from core.mention_sources.registry import get_source
from core.models import Mention
from core.output import save_draft

SKILL_MANIFEST = {
    "always": ["monitor/mention-evaluation", "monitor/sentiment-scoring"],
    "conditional": {},
    "post_processing": [],
}


def _format_mentions_table(mentions: list[Mention]) -> str:
    """Format mentions as a text table for stdout."""
    lines = [
        f"{'Source':<20} {'Title':<35} {'Rel':<5} {'Sentiment':<12} {'Score':<8} URL",
        "-" * 110,
    ]
    for m in mentions:
        title = (m.title or "")[:33]
        score = str(m.score) if m.score is not None else "N/A"
        rel = str(m.relevance_score) if m.relevance_score is not None else "N/A"
        lines.append(
            f"{m.source:<20} {title:<35} {rel:<5} {m.sentiment or 'N/A':<12} {score:<8} {m.url}"
        )
    return "\n".join(lines)


def _passes_pre_filter(mention: Mention, keyword: str, negative_keywords: list[str]) -> bool:
    """Cheap string-based pre-filter before LLM evaluation."""
    text = f"{mention.title or ''} {mention.content}".lower()

    # Must contain the keyword as a standalone word
    if not re.search(rf"\b{re.escape(keyword.lower())}\b", text):
        return False

    # Reject if any negative keyword appears as a standalone word
    for neg in negative_keywords:
        if re.search(rf"\b{re.escape(neg.lower())}\b", text):
            return False

    return True


def run(
    sources: list[str] | None = None,
    stdout_only: bool = True,
    no_cache: bool = False,
) -> list[Mention]:
    """Fetch and classify recent mentions.

    Args:
        sources: Filter to specific mention sources. None = all configured sources.
        stdout_only: Print to stdout only (default True for mentions check).
        no_cache: Skip cache.

    Returns:
        List of Mention objects with relevance and sentiment filled in.
    """
    config = get_config()
    active_sources = sources or config.monitor_mention_sources
    keyword = config.monitor_keyword
    lookback_days = config.monitor_mention_lookback_days
    min_relevance = config.monitor_min_relevance_score
    negative_keywords = config.monitor_negative_keywords
    since = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)

    # 1. Fetch mentions
    all_mentions: list[Mention] = []
    for source_name in active_sources:
        if source_name == "pypi":
            continue  # PyPI doesn't produce traditional mentions
        try:
            source = get_source(source_name)
            mentions = source.fetch_mentions(keyword, since)
            all_mentions.extend(mentions)
        except Exception:
            continue

    # 2. Pre-filter: cheap keyword/negative-keyword check
    pre_filtered = [
        m for m in all_mentions
        if _passes_pre_filter(m, keyword, negative_keywords)
    ]

    # 3. Evaluate relevance via LLM
    llm = LLMClient(agent_name="monitor_mentions")
    for mention in pre_filtered:
        result = evaluate_relevance(mention, llm)
        mention.relevance_score = result.relevance_score
        mention.relevance_reason = result.reason

    # 4. Filter by relevance
    relevant = [
        m for m in pre_filtered
        if m.relevance_score is not None and m.relevance_score >= min_relevance
    ]

    # 5. Classify sentiment (only on relevant mentions)
    for mention in relevant:
        mention.sentiment = classify_sentiment(mention, llm)

    # 6. Output
    table = _format_mentions_table(relevant)

    if stdout_only:
        print(f"\nMentions for '{keyword}' (last {lookback_days} days):")
        print(f"Sources: {', '.join(active_sources)}")
        print(f"Total: {len(all_mentions)} fetched, {len(pre_filtered)} pre-filtered, {len(relevant)} relevant\n")
        print(table)
    else:
        save_draft(
            agent_name="monitor-mentions",
            content=table,
            metadata={"mention_count": len(relevant), "sources": active_sources},
            stdout_only=False,
        )

    # 7. Save brief
    brief_data = {
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "sources": active_sources,
        "mentions": [m.model_dump() for m in relevant],
    }
    save_brief("mentions", brief_data)

    return relevant

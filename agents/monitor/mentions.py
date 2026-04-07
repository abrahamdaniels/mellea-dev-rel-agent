from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agents.monitor import classify_sentiment
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
        f"{'Source':<20} {'Title':<40} {'Sentiment':<12} {'Score':<8} URL",
        "-" * 100,
    ]
    for m in mentions:
        title = (m.title or "")[:38]
        score = str(m.score) if m.score is not None else "N/A"
        lines.append(
            f"{m.source:<20} {title:<40} {m.sentiment or 'N/A':<12} {score:<8} {m.url}"
        )
    return "\n".join(lines)


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
        List of Mention objects with sentiment filled in.
    """
    config = get_config()
    active_sources = sources or config.monitor_mention_sources
    keyword = config.monitor_keyword
    lookback_days = config.monitor_mention_lookback_days
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

    # 2. Classify sentiment
    llm = LLMClient(agent_name="monitor_mentions")
    for mention in all_mentions:
        mention.sentiment = classify_sentiment(mention, llm)

    # 3. Filter low-relevance mentions (score < 2 if score is available)
    filtered = [
        m for m in all_mentions
        if m.score is None or m.score >= 2
    ]

    # 4. Output
    table = _format_mentions_table(filtered)

    if stdout_only:
        print(f"\nMentions for '{keyword}' (last {lookback_days} days):")
        print(f"Sources: {', '.join(active_sources)}")
        print(f"Total: {len(all_mentions)} found, {len(filtered)} shown\n")
        print(table)
    else:
        save_draft(
            agent_name="monitor-mentions",
            content=table,
            metadata={"mention_count": len(filtered), "sources": active_sources},
            stdout_only=False,
        )

    # 5. Save brief
    brief_data = {
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "sources": active_sources,
        "mentions": [m.model_dump() for m in filtered],
    }
    save_brief("mentions", brief_data)

    return filtered

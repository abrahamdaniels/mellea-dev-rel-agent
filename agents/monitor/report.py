from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from agents.monitor import classify_sentiment
from core.briefs import save_brief
from core.config import get_config
from core.github_client import GitHubClient
from core.llm_client import LLMClient
from core.mention_sources.registry import get_source
from core.models import DraftOutput, Mention
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest

SKILL_MANIFEST = {
    "always": ["monitor/weekly-report", "monitor/sentiment-scoring"],
    "conditional": {},
    "post_processing": [],
}


def _fetch_github_stats() -> dict:
    """Fetch GitHub repo stats. Returns empty dict on failure."""
    try:
        client = GitHubClient()
        return client.get_repo_stats()
    except Exception:
        return {}


def _fetch_pypi_stats(keyword: str) -> dict:
    """Fetch PyPI stats for the keyword package."""
    try:
        from core.mention_sources.pypi import PyPISource

        source = PyPISource()
        since = datetime.now(tz=timezone.utc) - timedelta(days=7)
        mentions = source.fetch_mentions(keyword, since)
        if mentions:
            return mentions[0].metadata
        return {}
    except Exception:
        return {}


def _fetch_mentions(
    sources: list[str], keyword: str, lookback_days: int
) -> list[Mention]:
    """Fetch mentions from all specified sources."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
    all_mentions: list[Mention] = []

    for source_name in sources:
        try:
            source = get_source(source_name)
            if source_name == "pypi":
                continue  # PyPI stats handled separately
            mentions = source.fetch_mentions(keyword, since)
            all_mentions.extend(mentions)
        except Exception:
            continue

    return all_mentions


def run(
    sources: list[str] | None = None,
    stdout_only: bool = False,
    no_cache: bool = False,
) -> DraftOutput:
    """Generate a weekly monitor report.

    Args:
        sources: Filter to specific mention sources. None = all configured sources.
        stdout_only: Print to stdout only, skip file write.
        no_cache: Skip mention/stats cache.

    Returns:
        DraftOutput with the report markdown.
    """
    config = get_config()
    active_sources = sources or config.monitor_mention_sources
    keyword = config.monitor_keyword
    lookback_days = config.monitor_mention_lookback_days

    # 1. Fetch data
    github_stats = _fetch_github_stats()
    pypi_stats = _fetch_pypi_stats(keyword)
    mentions = _fetch_mentions(active_sources, keyword, lookback_days)

    # 2. Classify sentiment
    llm = LLMClient(agent_name="monitor_report")
    for mention in mentions:
        mention.sentiment = classify_sentiment(mention, llm)

    # 3. Load skills and generate report
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    # Format data for template
    github_stats_str = json.dumps(github_stats, indent=2, default=str) if github_stats else "N/A"
    pypi_stats_str = json.dumps(pypi_stats, indent=2, default=str) if pypi_stats else "N/A"

    content = llm.generate_with_template(
        "monitor/weekly_report",
        {
            "skills": skills_text,
            "github_stats": github_stats_str,
            "pypi_stats": pypi_stats_str,
            "mentions": mentions,
            "mention_count": len(mentions),
            "source_count": len(set(m.source for m in mentions)),
        },
    )

    # 4. Save brief (structured data for downstream agents)
    brief_data = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "github_stats": github_stats,
        "pypi_stats": pypi_stats,
        "mentions": [m.model_dump() for m in mentions],
        "mention_count": len(mentions),
        "sources_queried": active_sources,
    }
    save_brief("weekly-report", brief_data)

    # 5. Save draft (human-readable report)
    return save_draft(
        agent_name="monitor-report",
        content=content,
        metadata={
            "mention_count": len(mentions),
            "sources": active_sources,
        },
        stdout_only=stdout_only,
    )

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone

from core.briefs import load_brief, save_brief
from core.github_client import GitHubClient
from core.llm_client import LLMClient
from core.models import DraftOutput
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest

logger = logging.getLogger(__name__)

SKILL_MANIFEST = {
    "always": ["monitor/publications-tracking", "monitor/sentiment-scoring"],
    "conditional": {},
    "post_processing": [],
}


def _get_tracked_assets() -> list[dict]:
    """Fetch tracked assets from GitHub issues with asset-tracking label."""
    try:
        client = GitHubClient()
        issues = client.repo.get_issues(
            labels=["asset-tracking"], state="all"
        )
        assets = []
        for issue in issues:
            body = issue.body or ""
            asset = {
                "title": issue.title,
                "number": issue.number,
                "created_at": (
                    issue.created_at.isoformat() if issue.created_at else None
                ),
                "labels": [lb.name for lb in issue.labels],
            }
            # Extract fields from table in body
            for line in body.split("\n"):
                if "|" in line and "Type" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        asset["type"] = parts[2]
                if "|" in line and "Feature" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        asset["feature"] = parts[2]
                if "|" in line and "Location" in line:
                    parts = [p.strip() for p in line.split("|")]
                    for part in parts:
                        if part.startswith("http"):
                            asset["url"] = part
            assets.append(asset)
        return assets
    except Exception as exc:
        logger.warning("Could not fetch tracked assets: %s", exc)
        return []


def _load_mention_data() -> dict:
    """Load mention data from briefs. Returns empty dict on failure."""
    data = {}
    for brief_name in ["weekly-report", "mentions"]:
        try:
            brief = load_brief(brief_name)
            data[brief_name] = brief
        except FileNotFoundError:
            continue
    return data


def run(
    sources: list[str] | None = None,
    stdout_only: bool = False,
    no_cache: bool = False,
) -> DraftOutput:
    """Generate a publications performance report.

    Args:
        sources: Filter by asset type (blog, social_post, demo, etc.).
        stdout_only: Print to stdout only, skip file write.
        no_cache: Unused (kept for CLI consistency).

    Returns:
        DraftOutput with the report markdown.
    """
    # 1. Fetch tracked assets
    assets = _get_tracked_assets()

    # Filter by type if specified
    if sources:
        assets = [a for a in assets if a.get("type") in sources]

    # 2. Load mention briefs
    mention_data = _load_mention_data()

    # 3. Build statistics
    type_counts = Counter(a.get("type", "unknown") for a in assets)
    type_breakdown = json.dumps(dict(type_counts), indent=2)
    tracked_assets_str = json.dumps(assets, indent=2, default=str)
    mention_data_str = json.dumps(mention_data, indent=2, default=str)

    # 4. Generate report via LLM
    llm = LLMClient(agent_name="monitor_publications")
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    content = llm.generate_with_template(
        "monitor/publications_report",
        {
            "skills": skills_text,
            "tracked_assets": tracked_assets_str[:3000],
            "mention_data": mention_data_str[:3000],
            "asset_count": len(assets),
            "type_breakdown": type_breakdown,
        },
    )

    # 5. Save brief
    brief_data = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "asset_count": len(assets),
        "type_breakdown": dict(type_counts),
        "assets": assets,
    }
    save_brief("publications", brief_data)

    # 6. Save draft
    return save_draft(
        agent_name="monitor-publications",
        content=content,
        metadata={
            "asset_count": len(assets),
            "type_breakdown": dict(type_counts),
        },
        stdout_only=stdout_only,
    )

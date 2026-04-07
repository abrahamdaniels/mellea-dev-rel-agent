from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from core.briefs import load_brief
from core.config import get_config
from core.github_client import GitHubClient
from core.output import save_draft

logger = logging.getLogger(__name__)


def _get_tracked_urls() -> set[str]:
    """Fetch URLs from existing asset-tracking issues."""
    try:
        client = GitHubClient()
        issues = client.repo.get_issues(
            labels=["asset-tracking"], state="all"
        )
        urls: set[str] = set()
        for issue in issues:
            body = issue.body or ""
            # Extract URL from "| Location | URL |" table row
            for line in body.split("\n"):
                if "Location" in line and "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    for part in parts:
                        if part.startswith("http"):
                            urls.add(part)
        return urls
    except Exception as exc:
        logger.warning("Could not fetch tracked issues: %s", exc)
        return set()


def _scan_briefs() -> list[dict]:
    """Scan briefs for potential assets (mentions with URLs)."""
    found: list[dict] = []
    for brief_name in ["weekly-report", "mentions"]:
        try:
            data = load_brief(brief_name)
            mentions = data.get("mentions", [])
            for m in mentions:
                url = m.get("url", "")
                if url:
                    found.append({
                        "title": m.get("title", "Unknown"),
                        "url": url,
                        "source": f"brief:{brief_name}",
                        "platform": m.get("source", "unknown"),
                    })
        except FileNotFoundError:
            continue
    return found


def _scan_drafts() -> list[dict]:
    """Scan drafts directory for generated content that may have been published."""
    config = get_config()
    drafts_dir = Path(config.drafts_dir)
    found: list[dict] = []
    if drafts_dir.exists():
        for draft_file in sorted(drafts_dir.glob("*.md"))[-20:]:
            found.append({
                "title": draft_file.stem,
                "url": str(draft_file),
                "source": "drafts/",
                "platform": "local",
            })
    return found


def run(
    scan_platforms: list[str] | None = None,
    stdout_only: bool = True,
) -> dict:
    """Scan for untracked assets and report gaps.

    Args:
        scan_platforms: Platforms to scan. None = all configured.
        stdout_only: Print report to stdout (default) or save.

    Returns:
        Dict with tracked count, untracked list, and report text.
    """
    config = get_config()
    platforms = scan_platforms or config.tracker_scan_platforms

    # 1. Get already-tracked URLs
    tracked_urls = _get_tracked_urls()

    # 2. Scan for potential assets
    candidates = _scan_briefs() + _scan_drafts()

    # 3. Filter by platform if specified
    if scan_platforms:
        candidates = [
            c for c in candidates
            if c.get("platform") in platforms
        ]

    # 4. Find untracked
    untracked = [
        c for c in candidates
        if c["url"] not in tracked_urls
    ]

    # 5. Build report
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Asset Sync Report - {today}",
        "",
        f"## Tracked Assets: {len(tracked_urls)}",
        f"## Potentially Untracked: {len(untracked)}",
        "",
    ]

    if untracked:
        lines.append(
            "| Asset | Platform | Source | Suggested Action |"
        )
        lines.append("|---|---|---|---|")
        for item in untracked:
            title = item["title"][:40]
            url = item["url"]
            cmd = f'`devrel tracker log --context "{url}"`'
            lines.append(
                f"| {title} | {item['platform']} "
                f"| {item['source']} | {cmd} |"
            )
    else:
        lines.append("All known assets are tracked.")

    report = "\n".join(lines)

    if stdout_only:
        print(report)
    else:
        save_draft(
            agent_name="tracker-sync",
            content=report,
            metadata={
                "tracked": len(tracked_urls),
                "untracked": len(untracked),
            },
            stdout_only=False,
        )

    return {
        "tracked_count": len(tracked_urls),
        "untracked": untracked,
        "report": report,
    }

from __future__ import annotations

import json
from datetime import datetime, timezone

from core.briefs import load_brief
from core.context_resolver import resolve_context
from core.github_client import GitHubClient
from core.llm_client import LLMClient
from core.models import DraftOutput
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest

SKILL_MANIFEST = {
    "always": ["content/suggest", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": [],
}


def _load_briefs() -> str:
    """Load latest briefs and format as text. Gracefully handles missing briefs."""
    parts = []
    for brief_name in ["weekly-report", "mentions"]:
        try:
            data = load_brief(brief_name)
            parts.append(f"### {brief_name}\n\n{json.dumps(data, indent=2, default=str)}")
        except FileNotFoundError:
            parts.append(
                f"### {brief_name}\n\nNo data available "
                f"(run `devrel monitor report` first)"
            )
    return "\n\n".join(parts)


def _fetch_recent_github_activity() -> str:
    """Fetch recent releases and format as text."""
    try:
        client = GitHubClient()
        release = client.get_release()
        return (
            f"Latest release: {release['tag']} - {release['title']}\n"
            f"Published: {release.get('published_at', 'unknown')}\n"
            f"Notes: {release['body'][:300]}"
        )
    except Exception:
        return "No recent GitHub release data available."


def run(
    context_inputs: list[str] | None = None,
    stdout_only: bool = True,
    no_cache: bool = False,
) -> DraftOutput:
    """Generate content suggestions from monitor data.

    Args:
        context_inputs: Optional additional context. If None, reads latest briefs automatically.
        stdout_only: Print to stdout (default True -- suggestions are ephemeral).
        no_cache: Skip cache.

    Returns:
        DraftOutput with the suggestions markdown.
    """
    # 1. Load briefs automatically
    brief_content = _load_briefs()

    # 2. Resolve additional context if provided
    additional_context = ""
    if context_inputs:
        context_block = resolve_context(context_inputs, no_cache=no_cache)
        additional_context = context_block.combined_text

    # 3. Fetch recent GitHub activity
    github_activity = _fetch_recent_github_activity()

    # 4. Load skills and generate
    llm = LLMClient(agent_name="content_suggest")
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    content = llm.generate_with_template(
        "content/suggest",
        {
            "skills": skills_text,
            "brief_content": brief_content,
            "github_activity": github_activity,
            "additional_context": additional_context,
            "date": today,
        },
    )

    # 5. Save output
    return save_draft(
        agent_name="content-suggest",
        content=content,
        metadata={"date": today},
        stdout_only=stdout_only,
    )

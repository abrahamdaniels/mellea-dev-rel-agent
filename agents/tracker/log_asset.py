from __future__ import annotations

import logging
from datetime import datetime, timezone

from agents.tracker import detect_platform, infer_asset_type
from core.context_resolver import resolve_context
from core.github_client import GitHubClient
from core.llm_client import LLMClient
from core.models import AssetExtractionResult, AssetMetadata
from core.skill_loader import load_skill_content, resolve_manifest

logger = logging.getLogger(__name__)

SKILL_MANIFEST = {
    "always": ["tracker/asset-extraction", "tracker/issue-formatting"],
    "conditional": {},
    "post_processing": [],
}


def _extract_first_url(context_inputs: list[str]) -> str | None:
    """Return the first URL found in context inputs."""
    for inp in context_inputs:
        if inp.startswith("http://") or inp.startswith("https://"):
            return inp
    return None


def _extract_metadata_via_llm(
    llm: LLMClient, context_text: str
) -> AssetExtractionResult:
    """Use LLM to extract asset metadata from context."""
    return llm.generate_structured(
        prompt=(
            "Extract metadata from this DevRel asset. "
            "Return the asset type, title, primary Mellea feature, "
            "and sentiment.\n\n"
            f"Content:\n{context_text[:2000]}"
        ),
        output_type=AssetExtractionResult,
        requirements=[
            "asset_type must be one of: blog, social_post, ibm_article, demo, talk",
            "sentiment must be one of: positive, negative, neutral, mixed",
        ],
    )


def run(
    context_inputs: list[str],
    asset_type: str | None = None,
    title: str | None = None,
    link: str | None = None,
    feature: str | None = None,
    no_cache: bool = False,
    dry_run: bool = False,
) -> dict:
    """Log a published asset to the GitHub project board.

    Args:
        context_inputs: URL to published asset or description text.
        asset_type: Override asset type.
        title: Override title.
        link: Override URL.
        feature: Override feature.
        no_cache: Skip context cache.
        dry_run: Print issue body without creating.

    Returns:
        Dict with issue_number (or None if dry_run) and metadata.
    """
    # 1. Resolve context
    context_block = resolve_context(context_inputs, no_cache=no_cache)
    context_text = context_block.combined_text

    # 2. Detect platform from first URL
    first_url = link or _extract_first_url(context_inputs)
    platform = detect_platform(first_url) if first_url else None
    inferred_type = infer_asset_type(first_url) if first_url else None

    # 3. Extract metadata via LLM if needed
    llm = LLMClient(agent_name="tracker_log_asset")
    extracted = None
    if not all([asset_type, title, feature]):
        try:
            extracted = _extract_metadata_via_llm(llm, context_text)
        except Exception:
            logger.warning("LLM extraction failed, using defaults")

    # 4. Merge: explicit > extracted > inferred > defaults
    final_type = (
        asset_type
        or (extracted.asset_type if extracted else None)
        or inferred_type
        or "blog"
    )
    final_title = (
        title
        or (extracted.title if extracted else None)
        or "Untitled Asset"
    )
    final_feature = (
        feature
        or (extracted.feature if extracted else None)
        or "general"
    )
    final_sentiment = (
        (extracted.sentiment if extracted else None)
        or "neutral"
    )
    final_link = link or first_url or ""
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    metadata = AssetMetadata(
        asset_type=final_type,
        title=final_title,
        feature=final_feature,
        date=today,
        sentiment=final_sentiment,
        link=final_link,
        platform=platform,
    )

    # 5. Generate issue body via template
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    issue_body = llm.generate_with_template(
        "tracker/issue_body",
        {
            "skills": skills_text,
            "url": final_link,
            "context": context_text[:2000],
            "platform": platform or "",
            "explicit_type": asset_type or "",
            "explicit_title": title or "",
            "explicit_feature": feature or "",
        },
    )

    issue_title = f"[Asset] {final_type}: {final_title}"
    labels = ["asset-tracking", f"type:{final_type}"]

    # 6. Create or dry-run
    issue_number = None
    if dry_run:
        print(f"Title: {issue_title}")
        print(f"Labels: {', '.join(labels)}")
        print(f"\n{issue_body}")
    else:
        client = GitHubClient()
        issue_number = client.create_issue(
            title=issue_title,
            body=issue_body,
            labels=labels,
        )
        print(f"Created issue #{issue_number}: {issue_title}")

        # Add to project board if configured
        try:
            item_id = client.add_to_project_board(
                issue_number,
                fields={
                    "Type": final_type,
                    "Feature": final_feature,
                    "Sentiment": final_sentiment,
                },
            )
            print(f"Added to project board (item {item_id})")
        except (ValueError, Exception) as exc:
            logger.warning("Project board update skipped: %s", exc)

    return {
        "issue_number": issue_number,
        "metadata": metadata.model_dump(),
    }

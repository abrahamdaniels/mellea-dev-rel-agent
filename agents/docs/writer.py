from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from core.config import get_config
from core.context_resolver import resolve_context
from core.github_client import GitHubClient
from core.llm_client import LLMClient
from core.models import DocUpdatePlan
from core.skill_loader import load_skill_content, resolve_manifest

logger = logging.getLogger(__name__)

SKILL_MANIFEST = {
    "always": ["docs/writing-standards", "docs/llm-readability"],
    "conditional": {},
    "post_processing": [],
}


def _extract_file_blocks(raw_output: str) -> dict[str, str]:
    """Parse LLM output into {path: content} dict.

    Expects blocks delimited by ```file:path/to/file.md ... ```
    """
    pattern = r"```file:(\S+)\n(.*?)```"
    matches = re.findall(pattern, raw_output, re.DOTALL)
    return {path.strip(): content.strip() for path, content in matches}


def _create_branch_and_commit(
    client: GitHubClient,
    branch: str,
    files: dict[str, str],
    message: str,
) -> None:
    """Create branch and commit files using GitHub API (not local git)."""
    repo = client.repo
    default_branch = repo.default_branch
    ref = repo.get_git_ref(f"heads/{default_branch}")
    base_sha = ref.object.sha

    # Create branch
    repo.create_git_ref(f"refs/heads/{branch}", base_sha)

    # Create/update files on the branch
    for path, content in files.items():
        try:
            existing = repo.get_contents(path, ref=branch)
            repo.update_file(
                path, message, content, existing.sha, branch=branch
            )
        except Exception:
            repo.create_file(path, message, content, branch=branch)


def run(
    context_inputs: list[str],
    scope: str | None = None,
    no_cache: bool = False,
    dry_run: bool = False,
    stdout_only: bool = False,
) -> dict:
    """Generate documentation updates and create a PR.

    Args:
        context_inputs: PR URL, changelog, feature spec, or free text.
        scope: Limit to a specific docs directory or file.
        no_cache: Skip context cache.
        dry_run: Print changes without creating PR.
        stdout_only: Print to stdout only.

    Returns:
        Dict with pr_number (or None), affected_files, update_plan.
    """
    config = get_config()

    # 1. Resolve context
    context_block = resolve_context(context_inputs, no_cache=no_cache)
    context_text = context_block.combined_text

    # 2. Identify affected files via LLM
    llm = LLMClient(agent_name="docs_writer")

    try:
        update_plan = llm.generate_structured(
            prompt=(
                "Identify which documentation files need to be updated based "
                "on these changes. Consider the docs directory structure and "
                "which features or APIs are affected.\n\n"
                f"Changes:\n{context_text[:3000]}\n\n"
                f"Docs directory: {scope or config.docs_target_dir}"
            ),
            output_type=DocUpdatePlan,
            requirements=[
                "affected_files must be real file paths within the docs directory",
                "change_type must be one of: update, create, deprecate",
            ],
        )
    except Exception:
        logger.warning("LLM plan extraction failed, using scope as single file")
        update_plan = DocUpdatePlan(
            affected_files=[scope or f"{config.docs_target_dir}/index.md"],
            reason="Auto-detected from context",
            change_type="update",
        )

    # 3. Limit files
    affected = update_plan.affected_files[: config.docs_max_files_per_pr]

    # 4. Fetch existing content for affected files
    client = GitHubClient()
    affected_file_data = []
    for file_path in affected:
        try:
            content = client.get_file_content(file_path)
        except Exception:
            content = ""  # New file
        affected_file_data.append({"path": file_path, "content": content})

    # 5. Generate updated docs
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    raw_output = llm.generate_with_template(
        "docs/update",
        {
            "skills": skills_text,
            "context": context_text[:3000],
            "affected_files": affected_file_data,
        },
    )

    # 6. Parse file blocks from output
    file_updates = _extract_file_blocks(raw_output)

    if not file_updates:
        logger.warning("No file blocks extracted from LLM output")
        file_updates = {
            affected[0]: raw_output
        } if affected else {}

    # 7. Output or create PR
    pr_number = None

    if dry_run or stdout_only:
        for path, content in file_updates.items():
            print(f"\n--- {path} ---\n")
            print(content)
    else:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
        branch = f"{config.docs_branch_prefix}-{timestamp}"
        commit_msg = f"docs: update {len(file_updates)} file(s) from context"

        _create_branch_and_commit(client, branch, file_updates, commit_msg)

        pr_number = client.create_pr(
            branch=branch,
            title=f"[Docs] Update {len(file_updates)} file(s)",
            body=(
                "## Documentation Update\n\n"
                f"**Reason:** {update_plan.reason}\n"
                f"**Change type:** {update_plan.change_type}\n"
                f"**Files:** {', '.join(file_updates.keys())}\n\n"
                "Generated by `devrel docs update`."
            ),
        )
        print(f"Created PR #{pr_number} on branch {branch}")

    return {
        "pr_number": pr_number,
        "affected_files": list(file_updates.keys()),
        "update_plan": update_plan.model_dump(),
    }

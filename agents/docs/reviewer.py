from __future__ import annotations

import logging

from core.config import get_config
from core.context_resolver import resolve_context
from core.github_client import GitHubClient
from core.llm_client import LLMClient
from core.models import DocReviewReport
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest

logger = logging.getLogger(__name__)

SKILL_MANIFEST = {
    "always": ["docs/review-criteria", "docs/llm-readability"],
    "conditional": {},
    "post_processing": [],
}


def run(
    scope: str | None = None,
    context_inputs: list[str] | None = None,
    no_cache: bool = False,
    stdout_only: bool = True,
    create_issues: bool = False,
) -> dict:
    """Review documentation quality and LLM-readability.

    Args:
        scope: Docs directory or file to review (default: config.docs_target_dir).
        context_inputs: Optional API source code for accuracy cross-checking.
        no_cache: Skip context cache.
        stdout_only: Print report to stdout (default) or save.
        create_issues: Create GitHub issues for critical findings.

    Returns:
        Dict with files_reviewed, findings, report text.
    """
    config = get_config()
    client = GitHubClient()
    target = scope or config.docs_target_dir

    # 1. Discover docs files
    try:
        tree = client.get_tree(target)
        md_files = [
            f for f in tree
            if f["type"] == "file" and f["name"].endswith(".md")
        ]
    except Exception as exc:
        logger.warning("Could not list docs at %s: %s", target, exc)
        md_files = []

    if not md_files:
        report = f"No markdown files found in {target}."
        print(report)
        return {
            "files_reviewed": 0,
            "findings": [],
            "report": report,
        }

    # 2. Fetch content (cap at 20 files)
    files_data = []
    for f in md_files[:20]:
        try:
            content = client.get_file_content(f["path"])
            files_data.append({
                "path": f["path"],
                "size": f["size"],
                "content": content,
            })
        except Exception as exc:
            logger.warning("Could not read %s: %s", f["path"], exc)

    # 3. Optional API surface context
    api_surface = ""
    if context_inputs:
        ctx = resolve_context(context_inputs, no_cache=no_cache)
        api_surface = ctx.combined_text[:3000]

    # 4. Generate review
    llm = LLMClient(agent_name="docs_reviewer")
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    template_vars = {
        "skills": skills_text,
        "files": files_data,
        "api_surface": api_surface,
    }

    try:
        # Render template to prompt, then use generate_structured for parsing
        prompt = llm.render_template("docs/review_checklist", template_vars)
        review = llm.generate_structured(
            prompt=prompt,
            output_type=DocReviewReport,
            requirements=[
                "findings must reference actual file paths from the input",
                "severity must be one of: critical, warning, info",
            ],
        )
    except Exception:
        logger.warning("Structured review failed, falling back to text")
        raw_review = llm.generate_with_template(
            "docs/review_checklist",
            template_vars,
        )
        review = DocReviewReport(
            files_reviewed=len(files_data),
            findings=[],
            summary=raw_review[:1000],
        )

    # 5. Format report
    lines = [
        "# Documentation Review Report",
        "",
        f"**Files reviewed:** {review.files_reviewed}",
        f"**Total findings:** {len(review.findings)}",
        "",
    ]

    by_severity = {"critical": [], "warning": [], "info": []}
    for finding in review.findings:
        by_severity.get(finding.severity, by_severity["info"]).append(finding)

    for severity in ["critical", "warning", "info"]:
        findings = by_severity[severity]
        if findings:
            lines.append(f"## {severity.title()} ({len(findings)})")
            lines.append("")
            for f in findings:
                lines.append(f"- **{f.file_path}** [{f.category}]: {f.description}")
                if f.suggestion:
                    lines.append(f"  - Suggestion: {f.suggestion}")
            lines.append("")

    lines.append(f"## Summary\n\n{review.summary}")
    report = "\n".join(lines)

    # 6. Output
    if stdout_only:
        print(report)
    else:
        save_draft(
            agent_name="docs-review",
            content=report,
            metadata={
                "files_reviewed": review.files_reviewed,
                "findings_count": len(review.findings),
            },
            stdout_only=False,
        )

    # 7. Create issues for critical findings
    if create_issues:
        for finding in by_severity["critical"]:
            try:
                issue_num = client.create_issue(
                    title=(
                        f"[Docs Review] {finding.category}: "
                        f"{finding.file_path}"
                    ),
                    body=(
                        f"## Finding\n\n{finding.description}\n\n"
                        f"**File:** {finding.file_path}\n"
                        f"**Category:** {finding.category}\n"
                        f"**Severity:** {finding.severity}\n\n"
                        + (
                            f"## Suggestion\n\n{finding.suggestion}"
                            if finding.suggestion
                            else ""
                        )
                    ),
                    labels=["docs-review", f"severity:{finding.severity}"],
                )
                print(f"Created issue #{issue_num} for {finding.file_path}")
            except Exception as exc:
                logger.warning("Failed to create issue: %s", exc)

    return {
        "files_reviewed": review.files_reviewed,
        "findings": [f.model_dump() for f in review.findings],
        "report": report,
    }

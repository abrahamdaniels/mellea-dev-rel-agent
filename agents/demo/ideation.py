from __future__ import annotations

import json

from core.briefs import load_brief
from core.context_resolver import resolve_context
from core.llm_client import LLMClient
from core.models import DraftOutput
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest

SKILL_MANIFEST = {
    "always": ["demo/ideation", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": [],
}


def _load_briefs() -> str:
    """Load latest briefs for project intelligence context."""
    parts = []
    for brief_name in ["weekly-report", "mentions"]:
        try:
            data = load_brief(brief_name)
            parts.append(
                f"### {brief_name}\n\n{json.dumps(data, indent=2, default=str)}"
            )
        except FileNotFoundError:
            continue
    return "\n\n".join(parts) if parts else ""


def run(
    context_inputs: list[str] | None = None,
    stdout_only: bool = False,
) -> DraftOutput:
    """Generate demo concepts from context.

    Args:
        context_inputs: Feature descriptions, PR URLs, or free text.
        stdout_only: Print to stdout only, skip file write.

    Returns:
        DraftOutput with the concepts markdown.
    """
    # 1. Resolve context
    context_text = ""
    if context_inputs:
        context_block = resolve_context(context_inputs)
        context_text = context_block.combined_text

    # 2. Load briefs for project intelligence
    briefs = _load_briefs()

    # 3. Load skills and generate
    llm = LLMClient(agent_name="demo_ideation")
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    content = llm.generate_with_template(
        "demo/concept",
        {
            "skills": skills_text,
            "context": context_text or "General Mellea capabilities",
            "briefs": briefs,
        },
    )

    # 4. Save draft
    return save_draft(
        agent_name="demo-ideation",
        content=content,
        stdout_only=stdout_only,
    )

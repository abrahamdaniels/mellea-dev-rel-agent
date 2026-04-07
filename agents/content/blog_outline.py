from __future__ import annotations

from core.context_resolver import resolve_context
from core.llm_client import LLMClient
from core.models import DraftOutput
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest

SKILL_MANIFEST = {
    "always": ["content/blog-outline", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": [],
}


def run(
    context_inputs: list[str],
    stdout_only: bool = False,
    no_cache: bool = False,
) -> DraftOutput:
    """Generate a structured IBM Research blog outline."""
    context_block = resolve_context(context_inputs, no_cache=no_cache)
    context_text = context_block.combined_text

    llm = LLMClient(agent_name="blog_outline")

    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    content = llm.generate_with_template(
        "content/blog_outline",
        {
            "skills": skills_text,
            "context": context_text,
        },
    )

    return save_draft(
        agent_name="blog-outline",
        content=content,
        metadata={"context_sources": len(context_block.sources)},
        stdout_only=stdout_only,
    )

from __future__ import annotations

from core.context_resolver import resolve_context
from core.llm_client import LLMClient
from core.models import DraftOutput
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest, resolve_post_processing

SKILL_MANIFEST = {
    "always": ["content/technical-blog", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": ["content/de-llmify"],
}


def run(
    context_inputs: list[str],
    stdout_only: bool = False,
    no_cache: bool = False,
) -> DraftOutput:
    """Generate a technical blog post draft."""
    context_block = resolve_context(context_inputs, no_cache=no_cache)
    context_text = context_block.combined_text

    llm = LLMClient(agent_name="technical_blog")

    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    pp_paths = resolve_post_processing(SKILL_MANIFEST)
    post_processing_skills = load_skill_content(pp_paths)
    combined_skills = f"{skills_text}\n\n---\n\n{post_processing_skills}"

    content = llm.generate_with_template(
        "content/technical_blog",
        {
            "skills": combined_skills,
            "context": context_text,
        },
    )

    return save_draft(
        agent_name="technical-blog",
        content=content,
        metadata={"context_sources": len(context_block.sources)},
        stdout_only=stdout_only,
    )

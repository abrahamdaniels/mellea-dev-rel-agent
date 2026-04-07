from __future__ import annotations

from core.context_resolver import resolve_context
from core.llm_client import LLMClient
from core.models import DraftOutput
from core.output import save_draft
from core.skill_loader import load_skill_content, resolve_manifest, resolve_post_processing

SKILL_MANIFEST = {
    "always": ["content/social-post", "shared/mellea-knowledge"],
    "conditional": {
        "tone": {
            "personal": "shared/tone-personal",
            "ibm": "shared/tone-ibm",
        },
        "platform": {
            "twitter": "content/twitter-conventions",
            "linkedin": "content/linkedin-conventions",
        },
    },
    "post_processing": ["content/de-llmify"],
}


def _generate_for_platform(
    platform: str,
    tone: str,
    context_text: str,
    llm: LLMClient,
    post_processing_skills: str,
) -> str:
    flags = {"tone": tone, "platform": platform}
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags)
    skills_text = load_skill_content(skill_paths)

    # Combine post_processing skills into the prompt for the de-llmify pass
    combined_skills = f"{skills_text}\n\n---\n\n{post_processing_skills}"

    return llm.generate_with_template(
        "content/social_post",
        {
            "skills": combined_skills,
            "context": context_text,
            "platform": platform,
            "tone": tone,
        },
    )


def run(
    context_inputs: list[str],
    tone: str = "personal",
    platform: str = "both",
    stdout_only: bool = False,
    no_cache: bool = False,
) -> list[DraftOutput]:
    """Generate social post drafts. Returns one DraftOutput per platform."""
    context_block = resolve_context(context_inputs, no_cache=no_cache)
    context_text = context_block.combined_text

    llm = LLMClient(agent_name="social_post")

    # Load post-processing skills once
    pp_paths = resolve_post_processing(SKILL_MANIFEST)
    post_processing_skills = load_skill_content(pp_paths)

    platforms = ["twitter", "linkedin"] if platform == "both" else [platform]
    outputs: list[DraftOutput] = []

    for p in platforms:
        content = _generate_for_platform(p, tone, context_text, llm, post_processing_skills)
        draft = save_draft(
            agent_name=f"social-post-{p}",
            content=content,
            metadata={"platform": p, "tone": tone},
            stdout_only=stdout_only,
        )
        outputs.append(draft)

    return outputs

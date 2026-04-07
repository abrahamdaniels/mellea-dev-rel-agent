from __future__ import annotations

import logging
import re
from pathlib import Path

from agents.demo import parse_concept_file
from core.context_resolver import resolve_context
from core.llm_client import LLMClient
from core.pipeline import StageResult
from core.skill_loader import load_skill_content, resolve_manifest

logger = logging.getLogger(__name__)

SKILL_MANIFEST = {
    "always": ["demo/code-generation", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": [],
}

_FILE_BLOCK_RE = re.compile(
    r"```(\S+)\s*\n(.*?)```", re.DOTALL
)


def _extract_files(text: str) -> dict[str, str]:
    """Extract filename->content pairs from markdown code blocks.

    Expects blocks like:
        ```main.py
        code here
        ```
    """
    files: dict[str, str] = {}
    for match in _FILE_BLOCK_RE.finditer(text):
        filename = match.group(1).strip()
        content = match.group(2)
        # Only keep files with recognizable extensions
        if "." in filename:
            files[filename] = content.rstrip("\n") + "\n"
    return files


def run(
    concept: str,
    context_inputs: list[str] | None = None,
    repair_context: str | None = None,
    attempt: int = 0,
    output_dir: str | None = None,
    **kwargs,
) -> StageResult:
    """Generate demo code from a concept.

    Args:
        concept: Concept text, file path, or path:N selector.
        context_inputs: Optional additional context.
        repair_context: Error output from a previous failed test run.
        attempt: Retry attempt number (0 = first try).
        output_dir: Directory to write files to.

    Returns:
        StageResult with output["path"] set to the demo directory.
    """
    # 1. Parse concept
    try:
        concept_text = parse_concept_file(concept)
    except (ValueError, FileNotFoundError) as exc:
        return StageResult(
            stage_name="generate",
            success=False,
            error_context=f"Failed to parse concept: {exc}",
        )

    # 2. Resolve additional context
    additional_context = ""
    if context_inputs:
        context_block = resolve_context(context_inputs)
        additional_context = context_block.combined_text

    # 3. Determine output directory
    if not output_dir:
        slug = re.sub(r"[^a-z0-9]+", "_", concept_text[:50].lower()).strip("_")
        output_dir = str(Path("demos") / slug)

    # 4. Load skills and generate
    llm = LLMClient(agent_name="demo_code_gen")
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    template_vars = {
        "skills": skills_text,
        "concept": concept_text,
        "context": additional_context,
        "repair_context": repair_context or "",
        "attempt": attempt,
    }

    raw_output = llm.generate_with_template("demo/code_gen", template_vars)

    # 5. Extract files from the response
    files = _extract_files(raw_output)
    if not files:
        return StageResult(
            stage_name="generate",
            success=False,
            error_context="LLM output did not contain any extractable code blocks.",
        )

    # 6. Write files to output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for filename, content in files.items():
        (out_path / filename).write_text(content, encoding="utf-8")

    logger.info("Generated %d files in %s", len(files), output_dir)

    return StageResult(
        stage_name="generate",
        success=True,
        output={"path": str(out_path), "concept": concept},
    )

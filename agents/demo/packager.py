from __future__ import annotations

import logging
import sys
from pathlib import Path

from core.llm_client import LLMClient
from core.pipeline import StageResult
from core.skill_loader import load_skill_content, resolve_manifest

logger = logging.getLogger(__name__)

SKILL_MANIFEST = {
    "always": ["demo/packaging", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": [],
}


def run(
    path: str,
    concept: str | None = None,
    test_result=None,
    stdout_only: bool = False,
    **kwargs,
) -> StageResult:
    """Package a demo directory with README and polish.

    Args:
        path: Directory containing the demo files.
        concept: Original concept description (optional, for README context).
        test_result: TestResult from test runner (optional).
        stdout_only: Print README to stdout instead of writing.

    Returns:
        StageResult with the packaged demo path.
    """
    demo_path = Path(path)

    if not demo_path.exists():
        return StageResult(
            stage_name="package",
            success=False,
            error_context=f"Demo path does not exist: {path}",
        )

    # Warn if no test results
    if test_result is None:
        print(
            "Warning: No test results available. Packaging untested demo.",
            file=sys.stderr,
        )

    # Read all Python files from the demo directory
    code_parts = []
    for py_file in sorted(demo_path.glob("*.py")):
        file_text = py_file.read_text(encoding="utf-8")
        code_parts.append(f"### {py_file.name}\n\n```python\n{file_text}```")

    code_content = "\n\n".join(code_parts) if code_parts else "No Python files found."

    # Format test output
    test_output = ""
    if test_result is not None:
        test_output = (
            f"Tests passed: {test_result.passed}\n"
            f"Total: {test_result.total_tests}, Failed: {test_result.failed_tests}\n"
        )
        if test_result.error_output:
            test_output += f"\nError output:\n{test_result.error_output}"

    # Load skills and generate README
    llm = LLMClient(agent_name="demo_packager")
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags={})
    skills_text = load_skill_content(skill_paths)

    raw_output = llm.generate_with_template(
        "demo/readme",
        {
            "skills": skills_text,
            "code_content": code_content,
            "test_output": test_output,
            "concept": concept or "No concept description provided.",
        },
    )

    # Write README
    if stdout_only:
        print(raw_output)
    else:
        readme_path = demo_path / "README.md"
        readme_path.write_text(raw_output, encoding="utf-8")
        logger.info("README written to %s", readme_path)

    stage_output = {"path": str(demo_path)}

    # Run post-hooks (fire-and-forget)
    if not kwargs.get("no_hooks", False):
        from core.hooks import run_post_hooks

        run_post_hooks("demo.packager", stage_output)

    return StageResult(
        stage_name="package",
        success=True,
        output=stage_output,
    )

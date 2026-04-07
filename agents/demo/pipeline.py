"""Demo pipeline: generate -> test -> package with retry on test failure."""

from __future__ import annotations

from agents.demo import code_gen, packager, test_runner
from core.config import get_config
from core.pipeline import Pipeline, StageResult


def _build_pipeline() -> Pipeline:
    config = get_config()
    return Pipeline(
        stages=[
            ("generate", code_gen.run),
            ("test", test_runner.run),
            ("package", packager.run),
        ],
        on_stage_failure={
            "test": {
                "action": "retry_previous",
                "retry_budget": config.demo_retry_budget,
                "feed_output": True,
            },
        },
    )


def run(
    concept: str,
    context_inputs: list[str] | None = None,
    output_dir: str | None = None,
) -> list[StageResult]:
    """Run the full demo pipeline: generate -> test -> package.

    Args:
        concept: Concept text, file path, or path:N selector.
        context_inputs: Optional additional context for code generation.
        output_dir: Override default output directory.

    Returns:
        List of StageResult for each stage that ran.
    """
    pipeline = _build_pipeline()
    initial_input = {
        "concept": concept,
        "context_inputs": context_inputs,
        "output_dir": output_dir,
    }
    return pipeline.run(initial_input)

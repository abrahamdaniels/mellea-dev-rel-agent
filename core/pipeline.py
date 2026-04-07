"""Reusable pipeline engine for chaining agent stages with retry logic."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

logger = logging.getLogger("pipeline")


@dataclass
class StageResult:
    """Result of a single pipeline stage execution."""

    stage_name: str
    success: bool
    output: dict = field(default_factory=dict)
    error_context: str | None = None


class Pipeline:
    """Sequential pipeline that chains stages with optional retry on failure.

    Each stage is a callable that accepts ``**kwargs`` and returns a
    ``StageResult``.  On success the stage's ``output`` dict is merged into
    the running kwargs for the next stage.  On failure the pipeline consults
    ``on_stage_failure`` for retry instructions.
    """

    def __init__(
        self,
        stages: list[tuple[str, Callable]],
        on_stage_failure: dict | None = None,
    ) -> None:
        self.stages = stages
        self.on_stage_failure = on_stage_failure or {}

    def run(self, initial_input: dict) -> list[StageResult]:
        """Run all stages sequentially.  Stop on unrecoverable failure."""
        if not self.stages:
            return []

        results: list[StageResult] = []
        current_input = dict(initial_input)

        for stage_name, stage_fn in self.stages:
            logger.info("Running stage: %s", stage_name)
            result = stage_fn(**current_input)

            if not result.success and stage_name in self.on_stage_failure:
                failure_config = self.on_stage_failure[stage_name]
                result = self._handle_failure(
                    stage_name, stage_fn, result, current_input, failure_config
                )

            results.append(result)

            if not result.success:
                logger.warning("Pipeline stopped: stage '%s' failed", stage_name)
                break

            current_input.update(result.output)

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_failure(
        self,
        stage_name: str,
        stage_fn: Callable,
        result: StageResult,
        previous_input: dict,
        config: dict,
    ) -> StageResult:
        """Retry the *previous* stage with failure context, then re-run."""
        if config.get("action") != "retry_previous":
            return result

        retry_budget: int = config.get("retry_budget", 1)
        prev_name, prev_fn = self._get_previous_stage(stage_name)

        for attempt in range(1, retry_budget + 1):
            logger.info(
                "Retrying '%s' (attempt %d/%d) after '%s' failure",
                prev_name,
                attempt,
                retry_budget,
                stage_name,
            )
            repair_input = {
                **previous_input,
                "repair_context": result.error_context,
                "attempt": attempt,
            }
            prev_result = prev_fn(**repair_input)
            if not prev_result.success:
                continue

            # Re-run the failing stage with updated output
            retry_input = {**previous_input, **prev_result.output}
            retry_result = stage_fn(**retry_input)
            if retry_result.success:
                return retry_result
            result = retry_result  # update error for next retry

        return result  # all retries exhausted

    def _get_previous_stage(self, stage_name: str) -> tuple[str, Callable]:
        """Return the stage immediately before *stage_name*."""
        for i, (name, _fn) in enumerate(self.stages):
            if name == stage_name:
                if i == 0:
                    raise ValueError(
                        f"Cannot retry previous stage: '{stage_name}' is the first stage"
                    )
                return self.stages[i - 1]
        raise ValueError(f"Stage '{stage_name}' not found in pipeline")

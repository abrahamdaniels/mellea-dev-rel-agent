from __future__ import annotations

import pytest

from core.pipeline import Pipeline, StageResult


def _ok_stage(**kwargs) -> StageResult:
    return StageResult(stage_name="ok", success=True, output={"from_ok": True})


def _fail_stage(**kwargs) -> StageResult:
    return StageResult(
        stage_name="fail", success=False, error_context="something broke"
    )


def test_three_stage_pipeline_runs_all():
    def stage_a(**kw):
        return StageResult(stage_name="a", success=True, output={"val": 1})

    def stage_b(**kw):
        assert kw.get("val") == 1
        return StageResult(stage_name="b", success=True, output={"val": 2})

    def stage_c(**kw):
        assert kw.get("val") == 2
        return StageResult(stage_name="c", success=True, output={"val": 3})

    pipeline = Pipeline(stages=[("a", stage_a), ("b", stage_b), ("c", stage_c)])
    results = pipeline.run({})

    assert len(results) == 3
    assert all(r.success for r in results)


def test_pipeline_stops_on_failure_without_retry():
    pipeline = Pipeline(stages=[("ok", _ok_stage), ("fail", _fail_stage)])
    results = pipeline.run({})

    assert len(results) == 2
    assert results[0].success is True
    assert results[1].success is False


def test_pipeline_retries_previous_stage_on_failure():
    call_counts = {"gen": 0, "test": 0}

    def gen_stage(**kw):
        call_counts["gen"] += 1
        ver = "v" + str(call_counts["gen"])
        return StageResult(stage_name="gen", success=True, output={"code": ver})

    def test_stage(**kw):
        call_counts["test"] += 1
        # Fail first time, pass second time
        if call_counts["test"] == 1:
            return StageResult(stage_name="test", success=False, error_context="test error")
        return StageResult(stage_name="test", success=True, output={"tested": True})

    pipeline = Pipeline(
        stages=[("gen", gen_stage), ("test", test_stage)],
        on_stage_failure={
            "test": {"action": "retry_previous", "retry_budget": 2},
        },
    )
    results = pipeline.run({})

    assert len(results) == 2
    assert results[-1].success is True
    assert call_counts["gen"] == 2  # original + 1 retry
    assert call_counts["test"] == 2  # original + 1 re-run


def test_retry_injects_repair_context_and_attempt():
    captured_kwargs = {}

    def gen_stage(**kw):
        captured_kwargs.update(kw)
        return StageResult(stage_name="gen", success=True, output={"code": "fixed"})

    def test_stage(**kw):
        return StageResult(stage_name="test", success=False, error_context="assertion failed")

    pipeline = Pipeline(
        stages=[("gen", gen_stage), ("test", test_stage)],
        on_stage_failure={
            "test": {"action": "retry_previous", "retry_budget": 1},
        },
    )
    pipeline.run({})

    assert captured_kwargs.get("repair_context") == "assertion failed"
    assert captured_kwargs.get("attempt") == 1


def test_retry_budget_exhaustion_stops_pipeline():
    gen_count = 0

    def gen_stage(**kw):
        nonlocal gen_count
        gen_count += 1
        return StageResult(stage_name="gen", success=True, output={})

    def always_fail(**kw):
        return StageResult(stage_name="test", success=False, error_context="always fails")

    pipeline = Pipeline(
        stages=[("gen", gen_stage), ("test", always_fail), ("pkg", _ok_stage)],
        on_stage_failure={
            "test": {"action": "retry_previous", "retry_budget": 2},
        },
    )
    results = pipeline.run({})

    assert len(results) == 2  # gen + test, pkg never reached
    assert results[-1].success is False
    assert gen_count == 3  # original + 2 retries


def test_get_previous_stage_raises_for_first_stage():
    pipeline = Pipeline(stages=[("first", _ok_stage), ("second", _ok_stage)])
    with pytest.raises(ValueError, match="first stage"):
        pipeline._get_previous_stage("first")


def test_empty_stages_returns_empty():
    pipeline = Pipeline(stages=[])
    results = pipeline.run({})
    assert results == []

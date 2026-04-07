from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.pipeline import StageResult


def _gen_ok(**kw):
    return StageResult(
        stage_name="generate", success=True,
        output={"path": "/tmp/demo", "concept": "test concept"},
    )


def _test_ok(**kw):
    p = kw.get("path", "/tmp/demo")
    return StageResult(stage_name="test", success=True, output={"path": p})


def _pkg_ok(**kw):
    p = kw.get("path", "/tmp/demo")
    return StageResult(stage_name="package", success=True, output={"path": p})


def _test_fail(**kw):
    return StageResult(
        stage_name="test", success=False, error_context="AssertionError: expected 1 got 2"
    )


def test_full_pipeline_runs_three_stages():
    with patch("agents.demo.pipeline.code_gen") as mock_gen, \
         patch("agents.demo.pipeline.test_runner") as mock_test, \
         patch("agents.demo.pipeline.packager") as mock_pkg, \
         patch("agents.demo.pipeline.get_config") as mock_cfg:

        mock_gen.run = _gen_ok
        mock_test.run = _test_ok
        mock_pkg.run = _pkg_ok
        mock_cfg.return_value = MagicMock(demo_retry_budget=2)

        from agents.demo.pipeline import run
        results = run(concept="Test concept")

    assert len(results) == 3
    assert all(r.success for r in results)


def test_test_failure_triggers_retry():
    call_counts = {"gen": 0, "test": 0}

    def gen_fn(**kw):
        call_counts["gen"] += 1
        return _gen_ok(**kw)

    def test_fn(**kw):
        call_counts["test"] += 1
        if call_counts["test"] == 1:
            return _test_fail(**kw)
        return _test_ok(**kw)

    with patch("agents.demo.pipeline.code_gen") as mock_gen, \
         patch("agents.demo.pipeline.test_runner") as mock_test, \
         patch("agents.demo.pipeline.packager") as mock_pkg, \
         patch("agents.demo.pipeline.get_config") as mock_cfg:

        mock_gen.run = gen_fn
        mock_test.run = test_fn
        mock_pkg.run = _pkg_ok
        mock_cfg.return_value = MagicMock(demo_retry_budget=2)

        from agents.demo.pipeline import run
        results = run(concept="Test concept")

    # Final result should be success (after retry)
    assert results[-1].success is True
    assert call_counts["gen"] >= 2


def test_retry_passes_repair_context():
    captured = {}

    def gen_fn(**kw):
        captured.update(kw)
        return _gen_ok(**kw)

    with patch("agents.demo.pipeline.code_gen") as mock_gen, \
         patch("agents.demo.pipeline.test_runner") as mock_test, \
         patch("agents.demo.pipeline.packager") as mock_pkg, \
         patch("agents.demo.pipeline.get_config") as mock_cfg:

        mock_gen.run = gen_fn
        mock_test.run = _test_fail
        mock_pkg.run = _pkg_ok
        mock_cfg.return_value = MagicMock(demo_retry_budget=1)

        from agents.demo.pipeline import run
        run(concept="Test concept")

    assert "repair_context" in captured
    assert "AssertionError" in captured["repair_context"]


def test_retry_budget_exhaustion():
    with patch("agents.demo.pipeline.code_gen") as mock_gen, \
         patch("agents.demo.pipeline.test_runner") as mock_test, \
         patch("agents.demo.pipeline.packager") as mock_pkg, \
         patch("agents.demo.pipeline.get_config") as mock_cfg:

        mock_gen.run = _gen_ok
        mock_test.run = _test_fail
        mock_pkg.run = _pkg_ok
        mock_cfg.return_value = MagicMock(demo_retry_budget=2)

        from agents.demo.pipeline import run
        results = run(concept="Test concept")

    # Pipeline should stop at test stage, package never runs
    assert len(results) == 2
    assert results[-1].success is False


def test_generate_failure_stops_before_test():
    def gen_fail(**kw):
        return StageResult(stage_name="generate", success=False, error_context="no code")

    with patch("agents.demo.pipeline.code_gen") as mock_gen, \
         patch("agents.demo.pipeline.test_runner") as mock_test, \
         patch("agents.demo.pipeline.packager") as mock_pkg, \
         patch("agents.demo.pipeline.get_config") as mock_cfg:

        mock_gen.run = gen_fail
        mock_test.run = _test_ok
        mock_pkg.run = _pkg_ok
        mock_cfg.return_value = MagicMock(demo_retry_budget=2)

        from agents.demo.pipeline import run
        results = run(concept="Test concept")

    assert len(results) == 1
    assert results[0].success is False

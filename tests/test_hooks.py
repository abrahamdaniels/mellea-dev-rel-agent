from __future__ import annotations

from unittest.mock import patch

from core.hooks import POST_HOOKS, _matches, run_post_hooks


def test_matches_exact():
    assert _matches("demo.packager", "demo.packager") is True


def test_matches_prefix():
    assert _matches("demo.packager.sub", "demo.packager") is True


def test_matches_no_partial():
    """demo.packagerX should NOT match demo.packager."""
    assert _matches("demo.packagerX", "demo.packager") is False


def test_matches_different():
    assert _matches("content.social", "demo.packager") is False


def test_post_hooks_registry_has_demo_packager():
    assert "demo.packager" in POST_HOOKS
    assert "tracker.log_asset" in POST_HOOKS["demo.packager"]


@patch("core.hooks._invoke_hook")
def test_run_post_hooks_invokes_matching(mock_invoke):
    """Matching hooks are invoked with agent output."""
    output = {"path": "/demos/example"}
    run_post_hooks("demo.packager", output)

    mock_invoke.assert_called_once_with("tracker.log_asset", output)


@patch("core.hooks._invoke_hook")
def test_run_post_hooks_skips_non_matching(mock_invoke):
    """Non-matching agent names don't trigger hooks."""
    run_post_hooks("content.social", {"path": "/drafts/tweet.md"})

    mock_invoke.assert_not_called()


@patch("core.hooks._invoke_hook")
def test_run_post_hooks_failure_is_logged(mock_invoke):
    """Hook failures are caught and don't propagate."""
    mock_invoke.side_effect = RuntimeError("hook crashed")

    # Should not raise
    run_post_hooks("demo.packager", {"path": "/demos/ex"})


@patch("agents.tracker.log_asset.run")
def test_invoke_hook_tracker_log_asset(mock_log_run):
    """tracker.log_asset hook calls the log_asset agent."""
    from core.hooks import _invoke_hook

    _invoke_hook("tracker.log_asset", {"path": "/demos/example"})

    mock_log_run.assert_called_once_with(
        context_inputs=["/demos/example"],
        asset_type="demo",
        dry_run=False,
    )


@patch("agents.tracker.log_asset.run")
def test_invoke_hook_no_path_logs_warning(mock_log_run):
    """Missing path in context skips log_asset invocation."""
    from core.hooks import _invoke_hook

    _invoke_hook("tracker.log_asset", {})

    mock_log_run.assert_not_called()


def test_invoke_hook_unknown_raises():
    """Unknown hook name raises ValueError."""
    import pytest

    from core.hooks import _invoke_hook

    with pytest.raises(ValueError, match="Unknown hook"):
        _invoke_hook("nonexistent.hook", {})

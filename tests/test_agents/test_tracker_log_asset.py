from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import AssetExtractionResult


@patch("agents.tracker.log_asset.GitHubClient")
@patch("agents.tracker.log_asset.LLMClient")
@patch("agents.tracker.log_asset.resolve_context")
def test_log_asset_dry_run(mock_resolve, mock_llm_cls, mock_gh_cls, capsys):
    """Dry run prints issue body without creating."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "Some blog about Mellea structured output"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.return_value = AssetExtractionResult(
        asset_type="blog",
        title="Mellea Structured Output Guide",
        feature="structured_output",
        sentiment="positive",
    )
    mock_llm.generate_with_template.return_value = "| Field | Value |\n|---|---|"

    from agents.tracker.log_asset import run

    result = run(
        context_inputs=["https://medium.com/@user/mellea-guide"],
        dry_run=True,
    )

    assert result["issue_number"] is None
    assert result["metadata"]["asset_type"] == "blog"
    assert result["metadata"]["title"] == "Mellea Structured Output Guide"
    captured = capsys.readouterr()
    assert "Title:" in captured.out


@patch("agents.tracker.log_asset.GitHubClient")
@patch("agents.tracker.log_asset.LLMClient")
@patch("agents.tracker.log_asset.resolve_context")
def test_log_asset_creates_issue(mock_resolve, mock_llm_cls, mock_gh_cls):
    """Non-dry-run creates a GitHub issue."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "Demo content"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.return_value = AssetExtractionResult(
        asset_type="demo",
        title="Streaming Demo",
        feature="streaming",
        sentiment="neutral",
    )
    mock_llm.generate_with_template.return_value = "## Asset Tracking\n..."

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.create_issue.return_value = 42
    mock_client.add_to_project_board.return_value = "item-id"

    from agents.tracker.log_asset import run

    result = run(
        context_inputs=["https://github.com/org/repo/tree/main/demos/ex"],
        dry_run=False,
    )

    assert result["issue_number"] == 42
    mock_client.create_issue.assert_called_once()
    call_kwargs = mock_client.create_issue.call_args
    assert "[Asset]" in call_kwargs.kwargs.get("title", call_kwargs[1].get("title", ""))


@patch("agents.tracker.log_asset.GitHubClient")
@patch("agents.tracker.log_asset.LLMClient")
@patch("agents.tracker.log_asset.resolve_context")
def test_explicit_overrides_take_priority(mock_resolve, mock_llm_cls, mock_gh_cls):
    """Explicit params override LLM extraction."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "content"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_with_template.return_value = "body"

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.create_issue.return_value = 50
    mock_client.add_to_project_board.return_value = "item-id"

    from agents.tracker.log_asset import run

    result = run(
        context_inputs=["https://example.com"],
        asset_type="talk",
        title="My Talk",
        feature="validation",
        dry_run=False,
    )

    assert result["metadata"]["asset_type"] == "talk"
    assert result["metadata"]["title"] == "My Talk"
    assert result["metadata"]["feature"] == "validation"
    # LLM extraction should not be called when all fields are provided
    mock_llm.generate_structured.assert_not_called()


@patch("agents.tracker.log_asset.GitHubClient")
@patch("agents.tracker.log_asset.LLMClient")
@patch("agents.tracker.log_asset.resolve_context")
def test_llm_extraction_failure_uses_defaults(
    mock_resolve, mock_llm_cls, mock_gh_cls
):
    """When LLM extraction fails, defaults are used."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "content"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.side_effect = RuntimeError("LLM down")
    mock_llm.generate_with_template.return_value = "body"

    from agents.tracker.log_asset import run

    result = run(
        context_inputs=["https://medium.com/@u/article"],
        dry_run=True,
    )

    # Falls back to inferred type from URL (blog) and defaults
    assert result["metadata"]["asset_type"] == "blog"
    assert result["metadata"]["title"] == "Untitled Asset"
    assert result["metadata"]["feature"] == "general"


@patch("agents.tracker.log_asset.GitHubClient")
@patch("agents.tracker.log_asset.LLMClient")
@patch("agents.tracker.log_asset.resolve_context")
def test_project_board_failure_does_not_raise(
    mock_resolve, mock_llm_cls, mock_gh_cls
):
    """Project board failure is logged but doesn't fail the agent."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "content"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.return_value = AssetExtractionResult(
        asset_type="blog", title="T", feature="f", sentiment="neutral",
    )
    mock_llm.generate_with_template.return_value = "body"

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.create_issue.return_value = 77
    mock_client.add_to_project_board.side_effect = ValueError("No project ID")

    from agents.tracker.log_asset import run

    result = run(context_inputs=["https://dev.to/u/post"], dry_run=False)

    # Issue still created successfully
    assert result["issue_number"] == 77

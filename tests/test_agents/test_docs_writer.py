from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import DocUpdatePlan


@patch("agents.docs.writer.GitHubClient")
@patch("agents.docs.writer.LLMClient")
@patch("agents.docs.writer.resolve_context")
def test_writer_dry_run_prints_output(mock_resolve, mock_llm_cls, mock_gh_cls, capsys):
    """Dry run prints generated docs without creating PR."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "Added new streaming API method"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.return_value = DocUpdatePlan(
        affected_files=["docs/api/streaming.md"],
        reason="New streaming method added",
        change_type="update",
    )
    mock_llm.generate_with_template.return_value = (
        "```file:docs/api/streaming.md\n# Streaming API\n\nUpdated content.\n```"
    )

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_file_content.return_value = "# Streaming API\n\nOld content."

    from agents.docs.writer import run

    result = run(context_inputs=["https://github.com/org/repo/pull/1"], dry_run=True)

    assert result["pr_number"] is None
    assert "docs/api/streaming.md" in result["affected_files"]
    captured = capsys.readouterr()
    assert "streaming" in captured.out.lower()


@patch("agents.docs.writer.GitHubClient")
@patch("agents.docs.writer.LLMClient")
@patch("agents.docs.writer.resolve_context")
def test_writer_creates_pr(mock_resolve, mock_llm_cls, mock_gh_cls):
    """Non-dry-run creates branch and PR."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "New validation feature"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.return_value = DocUpdatePlan(
        affected_files=["docs/guides/validation.md"],
        reason="New validation feature",
        change_type="create",
    )
    mock_llm.generate_with_template.return_value = (
        "```file:docs/guides/validation.md\n# Validation Guide\n\nNew guide.\n```"
    )

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_file_content.side_effect = Exception("Not found")
    mock_client.create_pr.return_value = 42
    mock_repo = MagicMock()
    mock_repo.default_branch = "main"
    mock_ref = MagicMock()
    mock_ref.object.sha = "abc123"
    mock_repo.get_git_ref.return_value = mock_ref
    mock_repo.get_contents.side_effect = Exception("Not found")
    mock_client.repo = mock_repo

    from agents.docs.writer import run

    result = run(context_inputs=["feature spec text"], dry_run=False)

    assert result["pr_number"] == 42
    mock_client.create_pr.assert_called_once()


@patch("agents.docs.writer.GitHubClient")
@patch("agents.docs.writer.LLMClient")
@patch("agents.docs.writer.resolve_context")
def test_writer_scope_limits_files(mock_resolve, mock_llm_cls, mock_gh_cls):
    """Scope parameter is passed to LLM for file identification."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "API changes"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.return_value = DocUpdatePlan(
        affected_files=["docs/api/core.md"],
        reason="API change",
        change_type="update",
    )
    mock_llm.generate_with_template.return_value = (
        "```file:docs/api/core.md\n# Core API\n\nUpdated.\n```"
    )

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_file_content.return_value = "# Core API\n\nOld."

    from agents.docs.writer import run

    run(context_inputs=["changes"], scope="docs/api", dry_run=True)

    # Verify scope was used in the generate_structured call
    call_args = mock_llm.generate_structured.call_args
    assert "docs/api" in call_args.kwargs.get("prompt", call_args[1].get("prompt", ""))


@patch("agents.docs.writer.GitHubClient")
@patch("agents.docs.writer.LLMClient")
@patch("agents.docs.writer.resolve_context")
def test_writer_loads_skills(mock_resolve, mock_llm_cls, mock_gh_cls):
    """Skill manifest loads writing-standards + llm-readability."""
    from agents.docs.writer import SKILL_MANIFEST

    assert "docs/writing-standards" in SKILL_MANIFEST["always"]
    assert "docs/llm-readability" in SKILL_MANIFEST["always"]


@patch("agents.docs.writer.GitHubClient")
@patch("agents.docs.writer.LLMClient")
@patch("agents.docs.writer.resolve_context")
def test_writer_file_extraction(mock_resolve, mock_llm_cls, mock_gh_cls):
    """File blocks are correctly extracted from LLM output."""
    from agents.docs.writer import _extract_file_blocks

    raw = (
        "Here are the updates:\n\n"
        "```file:docs/guide.md\n# Guide\n\nContent here.\n```\n\n"
        "```file:docs/api.md\n# API\n\nAPI docs.\n```"
    )

    result = _extract_file_blocks(raw)

    assert "docs/guide.md" in result
    assert "docs/api.md" in result
    assert "# Guide" in result["docs/guide.md"]
    assert "# API" in result["docs/api.md"]


@patch("agents.docs.writer.GitHubClient")
@patch("agents.docs.writer.LLMClient")
@patch("agents.docs.writer.resolve_context")
def test_writer_llm_plan_failure_uses_fallback(
    mock_resolve, mock_llm_cls, mock_gh_cls
):
    """When LLM plan extraction fails, fallback plan is used."""
    mock_ctx = MagicMock()
    mock_ctx.combined_text = "Some changes"
    mock_resolve.return_value = mock_ctx

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm.generate_structured.side_effect = RuntimeError("LLM down")
    mock_llm.generate_with_template.return_value = "Updated content"

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_file_content.return_value = "Old content"

    from agents.docs.writer import run

    result = run(context_inputs=["changes"], dry_run=True)

    # Should still produce output using fallback plan
    assert result["affected_files"] is not None
    assert len(result["affected_files"]) >= 1

from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import DocFinding, DocReviewReport


@patch("agents.docs.reviewer.GitHubClient")
@patch("agents.docs.reviewer.LLMClient")
def test_reviewer_discovers_and_reviews_files(mock_llm_cls, mock_gh_cls, capsys):
    """Reviewer discovers md files and generates findings."""
    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_tree.return_value = [
        {"name": "index.md", "path": "docs/index.md", "type": "file", "size": 500},
        {"name": "api.md", "path": "docs/api.md", "type": "file", "size": 1200},
    ]
    mock_client.get_file_content.side_effect = [
        "# Index\n\nWelcome to the docs.",
        "# API\n\ndef foo(): pass",
    ]

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm._jinja = MagicMock()
    template_mock = MagicMock()
    template_mock.render.return_value = "rendered prompt"
    mock_llm._jinja.get_template.return_value = template_mock

    mock_llm.generate_structured.return_value = DocReviewReport(
        files_reviewed=2,
        findings=[
            DocFinding(
                file_path="docs/api.md",
                severity="warning",
                category="missing_example",
                description="No code examples for API functions.",
                suggestion="Add usage examples.",
            ),
        ],
        summary="Documentation is functional but lacks examples.",
    )

    from agents.docs.reviewer import run

    result = run(stdout_only=True)

    assert result["files_reviewed"] == 2
    assert len(result["findings"]) == 1
    assert result["findings"][0]["category"] == "missing_example"
    captured = capsys.readouterr()
    assert "missing_example" in captured.out


@patch("agents.docs.reviewer.GitHubClient")
@patch("agents.docs.reviewer.LLMClient")
def test_reviewer_scope_filters_files(mock_llm_cls, mock_gh_cls):
    """Scope parameter is passed to get_tree."""
    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_tree.return_value = [
        {"name": "core.md", "path": "docs/api/core.md", "type": "file", "size": 800},
    ]
    mock_client.get_file_content.return_value = "# Core API"

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm._jinja = MagicMock()
    template_mock = MagicMock()
    template_mock.render.return_value = "rendered"
    mock_llm._jinja.get_template.return_value = template_mock

    mock_llm.generate_structured.return_value = DocReviewReport(
        files_reviewed=1,
        findings=[],
        summary="Good.",
    )

    from agents.docs.reviewer import run

    run(scope="docs/api", stdout_only=True)

    mock_client.get_tree.assert_called_once_with("docs/api")


@patch("agents.docs.reviewer.GitHubClient")
@patch("agents.docs.reviewer.LLMClient")
def test_reviewer_create_issues_for_critical(mock_llm_cls, mock_gh_cls):
    """Critical findings create GitHub issues when --create-issues is set."""
    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_tree.return_value = [
        {"name": "guide.md", "path": "docs/guide.md", "type": "file", "size": 300},
    ]
    mock_client.get_file_content.return_value = "# Guide"
    mock_client.create_issue.return_value = 55

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm._jinja = MagicMock()
    template_mock = MagicMock()
    template_mock.render.return_value = "rendered"
    mock_llm._jinja.get_template.return_value = template_mock

    mock_llm.generate_structured.return_value = DocReviewReport(
        files_reviewed=1,
        findings=[
            DocFinding(
                file_path="docs/guide.md",
                severity="critical",
                category="stale_api",
                description="API signature mismatch.",
                suggestion="Update to match current code.",
            ),
            DocFinding(
                file_path="docs/guide.md",
                severity="info",
                category="missing_section",
                description="Missing when-to-use section.",
            ),
        ],
        summary="Has critical issues.",
    )

    from agents.docs.reviewer import run

    run(create_issues=True, stdout_only=True)

    # Only critical findings create issues
    mock_client.create_issue.assert_called_once()
    call_kwargs = mock_client.create_issue.call_args
    assert "stale_api" in call_kwargs.kwargs.get("title", call_kwargs[1].get("title", ""))


@patch("agents.docs.reviewer.GitHubClient")
@patch("agents.docs.reviewer.LLMClient")
def test_reviewer_empty_docs_directory(mock_llm_cls, mock_gh_cls, capsys):
    """Empty docs directory returns zero findings."""
    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_tree.return_value = []

    from agents.docs.reviewer import run

    result = run(stdout_only=True)

    assert result["files_reviewed"] == 0
    assert result["findings"] == []


@patch("agents.docs.reviewer.GitHubClient")
@patch("agents.docs.reviewer.LLMClient")
def test_reviewer_structured_fallback(mock_llm_cls, mock_gh_cls, capsys):
    """When structured review fails, falls back to text."""
    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.get_tree.return_value = [
        {"name": "readme.md", "path": "docs/readme.md", "type": "file", "size": 100},
    ]
    mock_client.get_file_content.return_value = "# Readme"

    mock_llm = MagicMock()
    mock_llm_cls.return_value = mock_llm
    mock_llm._jinja = MagicMock()
    template_mock = MagicMock()
    template_mock.render.return_value = "rendered"
    mock_llm._jinja.get_template.return_value = template_mock

    mock_llm.generate_structured.side_effect = RuntimeError("LLM failed")
    mock_llm.generate_with_template.return_value = "Overall docs look okay."

    from agents.docs.reviewer import run

    result = run(stdout_only=True)

    assert result["files_reviewed"] == 1
    assert result["findings"] == []
    assert "okay" in result["report"].lower()


@patch("agents.docs.reviewer.GitHubClient")
@patch("agents.docs.reviewer.LLMClient")
def test_reviewer_loads_correct_skills(mock_llm_cls, mock_gh_cls):
    """Skill manifest loads review-criteria + llm-readability."""
    from agents.docs.reviewer import SKILL_MANIFEST

    assert "docs/review-criteria" in SKILL_MANIFEST["always"]
    assert "docs/llm-readability" in SKILL_MANIFEST["always"]

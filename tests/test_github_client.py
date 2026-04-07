from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from github import RateLimitExceededException

from core.config import DevRelConfig


def _make_client(config=None):
    """Create a GitHubClient with a test config."""
    cfg = config or DevRelConfig(github_token="test-token", github_repo="owner/repo")
    with patch("core.github_client.Github") as MockGithub:
        from core.github_client import GitHubClient

        client = GitHubClient(config=cfg)
        mock_gh = MockGithub.return_value
        return client, mock_gh


def test_get_pr_returns_expected_keys():
    client, mock_gh = _make_client()
    mock_pr = MagicMock()
    mock_pr.number = 42
    mock_pr.title = "Add feature"
    mock_pr.body = "Description here"
    mock_pr.state = "open"
    mock_pr.user.login = "testuser"
    mock_pr.additions = 10
    mock_pr.deletions = 3
    mock_pr.changed_files = 2
    mock_pr.merged = False
    mock_pr.html_url = "https://github.com/owner/repo/pull/42"
    mock_pr.labels = []
    mock_pr.get_files.return_value = []
    mock_pr.get_issue_comments.return_value = []

    mock_repo = MagicMock()
    mock_repo.get_pull.return_value = mock_pr
    client._repo = mock_repo

    result = client.get_pr(42)

    assert result["number"] == 42
    assert result["title"] == "Add feature"
    assert result["body"] == "Description here"
    assert result["state"] == "open"
    assert result["author"] == "testuser"
    assert result["diff_stats"]["additions"] == 10
    assert result["diff_stats"]["deletions"] == 3
    assert isinstance(result["changed_files"], list)
    assert isinstance(result["comments"], list)


def test_get_issue_returns_expected_keys():
    client, mock_gh = _make_client()
    mock_issue = MagicMock()
    mock_issue.number = 10
    mock_issue.title = "Bug report"
    mock_issue.body = "Something broken"
    mock_issue.state = "open"
    mock_issue.user.login = "reporter"
    mock_issue.labels = []
    mock_issue.get_comments.return_value = []
    mock_issue.html_url = "https://github.com/owner/repo/issues/10"

    mock_repo = MagicMock()
    mock_repo.get_issue.return_value = mock_issue
    client._repo = mock_repo

    result = client.get_issue(10)

    assert result["number"] == 10
    assert result["title"] == "Bug report"
    assert result["state"] == "open"
    assert result["author"] == "reporter"
    assert isinstance(result["labels"], list)
    assert isinstance(result["comments"], list)


def test_get_release_returns_latest():
    client, mock_gh = _make_client()
    mock_release = MagicMock()
    mock_release.tag_name = "v1.0.0"
    mock_release.title = "Version 1.0"
    mock_release.body = "Release notes"
    mock_release.html_url = "https://github.com/owner/repo/releases/tag/v1.0.0"
    mock_release.assets = []
    mock_release.published_at = None

    mock_repo = MagicMock()
    mock_repo.get_latest_release.return_value = mock_release
    client._repo = mock_repo

    result = client.get_release()

    assert result["tag"] == "v1.0.0"
    assert result["title"] == "Version 1.0"
    assert result["body"] == "Release notes"
    assert isinstance(result["assets"], list)


def test_get_repo_stats_returns_counts():
    client, mock_gh = _make_client()
    mock_repo = MagicMock()
    mock_repo.stargazers_count = 100
    mock_repo.forks_count = 25
    mock_repo.open_issues_count = 5
    mock_repo.get_contributors.return_value = iter([MagicMock(), MagicMock()])
    client._repo = mock_repo

    result = client.get_repo_stats()

    assert result["stars"] == 100
    assert result["forks"] == 25
    assert result["open_issues"] == 5
    assert result["contributors"] == 2


def test_create_issue_returns_issue_number():
    client, mock_gh = _make_client()
    mock_issue = MagicMock()
    mock_issue.number = 99
    mock_repo = MagicMock()
    mock_repo.create_issue.return_value = mock_issue
    client._repo = mock_repo

    result = client.create_issue("Title", "Body")

    assert result == 99
    mock_repo.create_issue.assert_called_once()


def test_retry_on_rate_limit():
    client, mock_gh = _make_client()
    mock_repo = MagicMock()
    mock_repo.stargazers_count = 50
    mock_repo.forks_count = 10
    mock_repo.open_issues_count = 2
    mock_repo.get_contributors.return_value = iter([])

    call_count = 0

    def _flaky_get_pull(n):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RateLimitExceededException(429, {}, {})
        mock_pr = MagicMock()
        mock_pr.number = n
        mock_pr.title = "Retried"
        mock_pr.body = ""
        mock_pr.state = "open"
        mock_pr.user.login = "u"
        mock_pr.additions = 0
        mock_pr.deletions = 0
        mock_pr.changed_files = 0
        mock_pr.merged = False
        mock_pr.html_url = "url"
        mock_pr.labels = []
        mock_pr.get_files.return_value = []
        mock_pr.get_issue_comments.return_value = []
        return mock_pr

    mock_repo.get_pull.side_effect = _flaky_get_pull
    client._repo = mock_repo
    client._retry.backoff_base_seconds = 0.01

    result = client.get_pr(1)
    assert result["title"] == "Retried"
    assert call_count == 2


def test_retry_exhaustion_raises():
    client, mock_gh = _make_client()
    mock_repo = MagicMock()
    mock_repo.get_pull.side_effect = RateLimitExceededException(429, {}, {})
    client._repo = mock_repo
    client._retry.max_retries = 2
    client._retry.backoff_base_seconds = 0.01

    with pytest.raises(RateLimitExceededException):
        client.get_pr(1)


def test_add_to_project_board_requires_project_id():
    """Missing project ID raises ValueError."""
    cfg = DevRelConfig(github_token="test-token", github_repo="owner/repo")
    with patch("core.github_client.Github"):
        from core.github_client import GitHubClient

        client = GitHubClient(config=cfg)

    with pytest.raises(ValueError, match="github_project_id"):
        client.add_to_project_board(1)


@patch("core.github_client.httpx.post")
def test_add_to_project_board_returns_item_id(mock_httpx_post):
    """Successful add returns the project item ID."""
    cfg = DevRelConfig(
        github_token="test-token",
        github_repo="owner/repo",
        github_project_id="PVT_123",
    )
    with patch("core.github_client.Github"):
        from core.github_client import GitHubClient

        client = GitHubClient(config=cfg)

    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_issue.raw_data = {"node_id": "I_abc123"}
    mock_repo.get_issue.return_value = mock_issue
    client._repo = mock_repo

    # Mock GraphQL responses: add item, then field lookup
    add_resp = MagicMock()
    add_resp.status_code = 200
    add_resp.json.return_value = {
        "data": {
            "addProjectV2ItemById": {"item": {"id": "PVTI_456"}}
        }
    }
    add_resp.raise_for_status = MagicMock()

    mock_httpx_post.return_value = add_resp

    item_id = client.add_to_project_board(1)

    assert item_id == "PVTI_456"
    mock_httpx_post.assert_called_once()


@patch("core.github_client.httpx.post")
def test_add_to_project_board_updates_fields(mock_httpx_post):
    """Custom fields trigger additional GraphQL mutations."""
    cfg = DevRelConfig(
        github_token="test-token",
        github_repo="owner/repo",
        github_project_id="PVT_123",
    )
    with patch("core.github_client.Github"):
        from core.github_client import GitHubClient

        client = GitHubClient(config=cfg)

    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_issue.raw_data = {"node_id": "I_abc123"}
    mock_repo.get_issue.return_value = mock_issue
    client._repo = mock_repo

    # Response sequence: add item, get fields, update field
    add_resp = MagicMock()
    add_resp.json.return_value = {
        "data": {"addProjectV2ItemById": {"item": {"id": "PVTI_456"}}}
    }
    add_resp.raise_for_status = MagicMock()

    fields_resp = MagicMock()
    fields_resp.json.return_value = {
        "data": {
            "node": {
                "fields": {
                    "nodes": [
                        {"id": "F_1", "name": "Type"},
                        {"id": "F_2", "name": "Feature"},
                    ]
                }
            }
        }
    }
    fields_resp.raise_for_status = MagicMock()

    update_resp = MagicMock()
    update_resp.json.return_value = {
        "data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_456"}}}
    }
    update_resp.raise_for_status = MagicMock()

    mock_httpx_post.side_effect = [add_resp, fields_resp, update_resp, update_resp]

    client.add_to_project_board(1, fields={"Type": "blog", "Feature": "streaming"})

    # add + fields lookup + 2 field updates = 4 calls
    assert mock_httpx_post.call_count == 4


def test_get_tree_returns_file_entries():
    """get_tree returns list of file dicts with correct keys."""
    client, mock_gh = _make_client()
    mock_file = MagicMock()
    mock_file.name = "index.md"
    mock_file.path = "docs/index.md"
    mock_file.type = "file"
    mock_file.size = 500

    mock_dir = MagicMock()
    mock_dir.name = "api"
    mock_dir.path = "docs/api"
    mock_dir.type = "dir"
    mock_dir.size = 0

    mock_repo = MagicMock()
    mock_repo.get_contents.return_value = [mock_file, mock_dir]
    mock_repo.default_branch = "main"
    client._repo = mock_repo

    result = client.get_tree("docs")

    assert len(result) == 2
    assert result[0]["name"] == "index.md"
    assert result[0]["path"] == "docs/index.md"
    assert result[0]["type"] == "file"
    assert result[1]["type"] == "dir"


def test_get_file_content_returns_string():
    """get_file_content returns decoded string."""
    client, mock_gh = _make_client()
    mock_content = MagicMock()
    mock_content.decoded_content = b"# API Guide\n\nSome content."

    mock_repo = MagicMock()
    mock_repo.get_contents.return_value = mock_content
    mock_repo.default_branch = "main"
    client._repo = mock_repo

    result = client.get_file_content("docs/api.md")

    assert result == "# API Guide\n\nSome content."
    mock_repo.get_contents.assert_called_once_with("docs/api.md", ref="main")


def test_create_pr_returns_pr_number():
    """create_pr creates a pull request and returns its number."""
    client, mock_gh = _make_client()
    mock_pr = MagicMock()
    mock_pr.number = 88

    mock_repo = MagicMock()
    mock_repo.default_branch = "main"
    mock_repo.create_pull.return_value = mock_pr
    client._repo = mock_repo

    result = client.create_pr(
        branch="feature-branch",
        title="Test PR",
        body="PR body",
    )

    assert result == 88
    mock_repo.create_pull.assert_called_once_with(
        title="Test PR",
        body="PR body",
        head="feature-branch",
        base="main",
    )

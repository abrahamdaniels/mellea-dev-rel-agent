from __future__ import annotations

from unittest.mock import MagicMock, patch


@patch("agents.tracker.sync.GitHubClient")
@patch("agents.tracker.sync.get_config")
@patch("agents.tracker.sync.load_brief")
def test_sync_reports_untracked(mock_brief, mock_config, mock_gh_cls, capsys):
    """Untracked assets appear in the report."""
    cfg = MagicMock()
    cfg.tracker_scan_platforms = []
    cfg.drafts_dir = "/nonexistent"
    mock_config.return_value = cfg

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.repo.get_issues.return_value = []

    mock_brief.return_value = {
        "mentions": [
            {"title": "Blog Post", "url": "https://example.com/blog", "source": "twitter"},
        ]
    }

    from agents.tracker.sync import run

    result = run(stdout_only=True)

    assert result["tracked_count"] == 0
    assert len(result["untracked"]) >= 1
    assert "Blog Post" in result["report"]


@patch("agents.tracker.sync.GitHubClient")
@patch("agents.tracker.sync.get_config")
@patch("agents.tracker.sync.load_brief")
def test_sync_filters_tracked_urls(mock_brief, mock_config, mock_gh_cls, capsys):
    """Already-tracked URLs are excluded from untracked list."""
    cfg = MagicMock()
    cfg.tracker_scan_platforms = []
    cfg.drafts_dir = "/nonexistent"
    mock_config.return_value = cfg

    # Simulate a tracked issue with URL in body
    mock_issue = MagicMock()
    mock_issue.body = "| Location | https://example.com/blog |"
    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.repo.get_issues.return_value = [mock_issue]

    mock_brief.return_value = {
        "mentions": [
            {"title": "Blog Post", "url": "https://example.com/blog", "source": "twitter"},
        ]
    }

    from agents.tracker.sync import run

    result = run(stdout_only=True)

    assert len(result["untracked"]) == 0
    assert "All known assets are tracked" in result["report"]


@patch("agents.tracker.sync.GitHubClient")
@patch("agents.tracker.sync.get_config")
@patch("agents.tracker.sync.load_brief")
def test_sync_platform_filter(mock_brief, mock_config, mock_gh_cls):
    """Platform filter narrows candidate list."""
    cfg = MagicMock()
    cfg.tracker_scan_platforms = []
    cfg.drafts_dir = "/nonexistent"
    mock_config.return_value = cfg

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.repo.get_issues.return_value = []

    mock_brief.return_value = {
        "mentions": [
            {"title": "Tweet", "url": "https://x.com/status/1", "source": "twitter"},
            {"title": "Blog", "url": "https://medium.com/post", "source": "medium"},
        ]
    }

    from agents.tracker.sync import run

    result = run(scan_platforms=["twitter"], stdout_only=True)

    # Only twitter mention should be in untracked
    urls = [u["url"] for u in result["untracked"]]
    assert "https://x.com/status/1" in urls
    assert "https://medium.com/post" not in urls


@patch("agents.tracker.sync.GitHubClient")
@patch("agents.tracker.sync.get_config")
@patch("agents.tracker.sync.load_brief")
def test_sync_missing_brief_handled(mock_brief, mock_config, mock_gh_cls):
    """Missing brief files don't crash sync."""
    cfg = MagicMock()
    cfg.tracker_scan_platforms = []
    cfg.drafts_dir = "/nonexistent"
    mock_config.return_value = cfg

    mock_client = MagicMock()
    mock_gh_cls.return_value = mock_client
    mock_client.repo.get_issues.return_value = []

    mock_brief.side_effect = FileNotFoundError("No brief")

    from agents.tracker.sync import run

    result = run(stdout_only=True)

    assert result["tracked_count"] == 0
    assert len(result["untracked"]) == 0

"""Tests for core/context_resolver.py"""
from unittest.mock import MagicMock, patch

import pytest

from core.context_resolver import _resolve_single, resolve_context
from core.models import ContextBlock

# --- Input type detection ---

def test_raw_text_passthrough():
    source = _resolve_single("Just some raw text about streaming", no_cache=True)
    assert source.source_type == "text"
    assert source.content == "Just some raw text about streaming"


def test_local_file(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("# Notes\nSome notes here.")
    source = _resolve_single(str(f), no_cache=True)
    assert source.source_type == "file"
    assert source.title == "notes.md"
    assert "Some notes here" in source.content


def test_github_pr_url_detected():
    url = "https://github.com/generative-computing/mellea/pull/676"
    with patch("core.context_resolver.GitHubClient") as MockClient:
        instance = MockClient.return_value
        instance.get_pr.return_value = {
            "number": 676,
            "title": "Add streaming support",
            "body": "This adds streaming.",
            "state": "merged",
            "author": "user",
            "diff_stats": {"additions": 100, "deletions": 10, "changed_files": 5},
            "changed_files": [],
            "comments": [],
            "labels": [],
            "merged": True,
            "url": url,
        }
        source = _resolve_single(url, no_cache=True)
    assert source.source_type == "github_pr"
    assert source.title == "Add streaming support"
    assert "streaming" in source.content.lower()


def test_github_issue_url_detected():
    url = "https://github.com/generative-computing/mellea/issues/123"
    with patch("core.context_resolver.GitHubClient") as MockClient:
        instance = MockClient.return_value
        instance.get_issue.return_value = {
            "number": 123,
            "title": "Bug: retry not working",
            "body": "Steps to reproduce...",
            "state": "open",
            "author": "user",
            "labels": ["bug"],
            "comments": [],
            "url": url,
        }
        source = _resolve_single(url, no_cache=True)
    assert source.source_type == "github_issue"
    assert source.title == "Bug: retry not working"


def test_web_url_detected():
    url = "https://example.com/some-article"
    with patch("core.context_resolver.httpx") as mock_httpx:
        mock_response = MagicMock()
        mock_response.text = (
            "<html><head><title>Test Page</title></head>"
            "<body><p>Hello world</p></body></html>"
        )
        mock_response.status_code = 200
        mock_httpx.get.return_value = mock_response
        source = _resolve_single(url, no_cache=True)
    assert source.source_type == "web"
    assert source.title == "Test Page"
    assert "Hello world" in source.content


# --- Context block assembly ---

def test_mixed_inputs_produce_combined_text(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("Feature notes.")

    sources = resolve_context(["raw text here", str(f)], no_cache=True)
    assert isinstance(sources, ContextBlock)
    assert len(sources.sources) == 2
    assert "raw text here" in sources.combined_text
    assert "Feature notes" in sources.combined_text
    assert "---" in sources.combined_text  # separator present


def test_combined_text_has_source_headers(tmp_path):
    f = tmp_path / "info.md"
    f.write_text("Content here.")
    block = resolve_context([str(f)], no_cache=True)
    assert "## Source:" in block.combined_text


# --- Caching ---

def test_cache_hit_skips_second_fetch(tmp_path):
    url = "https://github.com/generative-computing/mellea/pull/999"
    pr_data = {
        "number": 999,
        "title": "Cached PR",
        "body": "Body",
        "state": "open",
        "author": "user",
        "diff_stats": {"additions": 1, "deletions": 0, "changed_files": 1},
        "changed_files": [],
        "comments": [],
        "labels": [],
        "merged": False,
        "url": url,
    }

    with patch("core.context_resolver.GitHubClient") as MockClient, \
         patch("core.context_resolver.get_config") as mock_cfg:
        mock_cfg.return_value.cache_dir = str(tmp_path)
        mock_cfg.return_value.cache_ttl_seconds = 3600
        mock_cfg.return_value.github_token = ""
        mock_cfg.return_value.github_repo = "generative-computing/mellea"

        instance = MockClient.return_value
        instance.get_pr.return_value = pr_data

        # First call — hits GitHub
        _resolve_single(url, no_cache=False)
        assert instance.get_pr.call_count == 1

        # Second call — should read from cache, not call GitHub again
        result = _resolve_single(url, no_cache=False)
        assert instance.get_pr.call_count == 1  # still 1 — cache was used
        assert result.title == "Cached PR"


def test_cache_ttl_expired_refetches(tmp_path):
    """When cache is older than TTL, the resolver should re-fetch."""
    import json
    import time

    url = "https://github.com/generative-computing/mellea/pull/888"
    pr_data = {
        "number": 888,
        "title": "Stale PR",
        "body": "Body",
        "state": "open",
        "author": "user",
        "diff_stats": {"additions": 1, "deletions": 0, "changed_files": 1},
        "changed_files": [],
        "comments": [],
        "labels": [],
        "merged": False,
        "url": url,
    }

    from core.context_resolver import _cache_key

    # Write a stale cache file (2 hours old, TTL is 1 hour)
    cache_file = tmp_path / f"{_cache_key(url)}.json"
    stale_data = {
        "fetched_at": time.time() - 7200,
        "data": {
            "source_type": "github_pr",
            "origin": url,
            "title": "Old Cached PR",
            "content": "old",
            "metadata": {},
        },
    }
    cache_file.write_text(json.dumps(stale_data))

    with patch("core.context_resolver.GitHubClient") as MockClient, \
         patch("core.context_resolver.get_config") as mock_cfg:
        mock_cfg.return_value.cache_dir = str(tmp_path)
        mock_cfg.return_value.cache_ttl_seconds = 3600
        mock_cfg.return_value.github_token = ""
        mock_cfg.return_value.github_repo = "generative-computing/mellea"

        instance = MockClient.return_value
        instance.get_pr.return_value = pr_data

        result = _resolve_single(url, no_cache=False)

    # Should have re-fetched because cache was expired
    assert instance.get_pr.call_count == 1
    assert result.title == "Stale PR"


def test_no_cache_bypasses_existing_cache(tmp_path):
    """When no_cache=True, the resolver ignores existing cache and re-fetches."""
    import json
    import time

    url = "https://github.com/generative-computing/mellea/pull/777"
    pr_data = {
        "number": 777,
        "title": "Fresh PR",
        "body": "Body",
        "state": "open",
        "author": "user",
        "diff_stats": {"additions": 1, "deletions": 0, "changed_files": 1},
        "changed_files": [],
        "comments": [],
        "labels": [],
        "merged": False,
        "url": url,
    }

    from core.context_resolver import _cache_key

    # Write a valid (non-expired) cache file
    cache_file = tmp_path / f"{_cache_key(url)}.json"
    cached_data = {
        "fetched_at": time.time(),
        "data": {
            "source_type": "github_pr",
            "origin": url,
            "title": "Cached PR",
            "content": "cached",
            "metadata": {},
        },
    }
    cache_file.write_text(json.dumps(cached_data))

    with patch("core.context_resolver.GitHubClient") as MockClient, \
         patch("core.context_resolver.get_config") as mock_cfg:
        mock_cfg.return_value.cache_dir = str(tmp_path)
        mock_cfg.return_value.cache_ttl_seconds = 3600
        mock_cfg.return_value.github_token = ""
        mock_cfg.return_value.github_repo = "generative-computing/mellea"

        instance = MockClient.return_value
        instance.get_pr.return_value = pr_data

        result = _resolve_single(url, no_cache=True)

    # Should have fetched fresh despite valid cache
    assert instance.get_pr.call_count == 1
    assert result.title == "Fresh PR"


@pytest.mark.integration
def test_real_github_pr():
    """Integration test: fetch a real PR from GitHub. Requires DEVREL_GITHUB_TOKEN."""
    import os

    from github import GithubException

    if not os.environ.get("DEVREL_GITHUB_TOKEN"):
        pytest.skip("DEVREL_GITHUB_TOKEN not set")

    url = "https://github.com/generative-computing/mellea/pull/1"
    try:
        source = _resolve_single(url, no_cache=True)
    except GithubException.UnknownObjectException:
        pytest.skip("PR not found or not accessible with current token")

    assert source.source_type == "github_pr"
    assert source.title is not None

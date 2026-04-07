from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from core.mention_sources.github_discussions import GitHubDiscussionsSource

SAMPLE_GRAPHQL_RESPONSE = {
    "data": {
        "search": {
            "edges": [
                {
                    "node": {
                        "title": "Using Mellea for structured output",
                        "bodyText": "I tried Mellea and it works great for validation.",
                        "url": "https://github.com/org/repo/discussions/42",
                        "createdAt": "2024-04-05T12:00:00Z",
                        "author": {"login": "contributor1"},
                        "upvoteCount": 5,
                        "repository": {"nameWithOwner": "org/repo"},
                    }
                },
                {
                    "node": {
                        "title": "Mellea question",
                        "bodyText": "How do I use rejection sampling?",
                        "url": "https://github.com/org/repo/discussions/43",
                        "createdAt": "2024-04-04T08:30:00Z",
                        "author": {"login": "newuser"},
                        "upvoteCount": 1,
                        "repository": {"nameWithOwner": "org/repo"},
                    }
                },
            ]
        }
    }
}


def _make_mock_response(data):
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


def test_fetch_mentions_parses_graphql_response():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = _make_mock_response(SAMPLE_GRAPHQL_RESPONSE)

    import core.mention_sources.github_discussions as mod

    with patch.object(mod, "httpx") as mock_httpx, \
         patch.object(mod, "get_config") as mock_cfg:
        mock_httpx.post.return_value = mock_resp
        mock_httpx.HTTPError = Exception
        mock_cfg.return_value = MagicMock(
            github_token="fake-token",
            github_repo="generative-computing/mellea",
        )

        source = GitHubDiscussionsSource()
        mentions = source.fetch_mentions("mellea", since)

    assert len(mentions) >= 2
    assert mentions[0].source == "github_discussions"
    assert mentions[0].url.startswith("https://github.com")
    assert mentions[0].author == "contributor1"


def test_is_available_false_without_token():
    import core.mention_sources.github_discussions as mod

    with patch.object(mod, "get_config") as mock_cfg:
        mock_cfg.return_value = MagicMock(github_token="")
        source = GitHubDiscussionsSource()
        assert source.is_available() is False


def test_is_available_true_with_token():
    import core.mention_sources.github_discussions as mod

    with patch.object(mod, "get_config") as mock_cfg:
        mock_cfg.return_value = MagicMock(github_token="ghp_abc123")
        source = GitHubDiscussionsSource()
        assert source.is_available() is True


def test_empty_response_returns_empty_list():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    empty_resp = _make_mock_response({"data": {"search": {"edges": []}}})

    import core.mention_sources.github_discussions as mod

    with patch.object(mod, "httpx") as mock_httpx, \
         patch.object(mod, "get_config") as mock_cfg:
        mock_httpx.post.return_value = empty_resp
        mock_httpx.HTTPError = Exception
        mock_cfg.return_value = MagicMock(
            github_token="fake-token",
            github_repo="generative-computing/mellea",
        )

        source = GitHubDiscussionsSource()
        mentions = source.fetch_mentions("mellea", since)

    assert mentions == []

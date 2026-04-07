from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from core.mention_sources.reddit import RedditSource

SAMPLE_REDDIT_RESPONSE = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "Mellea is great for structured output",
                    "selftext": "Used it in production and it works well.",
                    "permalink": "/r/MachineLearning/comments/abc123/mellea_is_great/",
                    "author": "dev_user",
                    "created_utc": 1712400000,  # 2024-04-06
                    "score": 42,
                    "subreddit": "MachineLearning",
                    "num_comments": 5,
                }
            },
            {
                "data": {
                    "title": "Another Mellea post",
                    "selftext": "",
                    "permalink": "/r/Python/comments/def456/another_post/",
                    "author": "py_fan",
                    "created_utc": 1712300000,
                    "score": 10,
                    "subreddit": "Python",
                    "num_comments": 2,
                }
            },
        ]
    }
}


def _mock_httpx_get(response):
    """Create a patched httpx.get that returns the given response."""
    import core.mention_sources.reddit as mod
    return patch.object(mod, "httpx", **{"get.return_value": response, "HTTPError": Exception})


def test_reddit_parses_mentions():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_REDDIT_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    import core.mention_sources.reddit as mod

    with patch.object(mod, "httpx") as mock_httpx, \
         patch.object(mod, "time"):
        mock_httpx.get.return_value = mock_resp
        mock_httpx.HTTPError = Exception

        source = RedditSource()
        mentions = source.fetch_mentions("mellea", since)

    assert len(mentions) >= 2
    assert mentions[0].source == "reddit"
    assert "mellea" in mentions[0].title.lower()


def test_reddit_deduplicates_by_url():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_REDDIT_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    import core.mention_sources.reddit as mod

    with patch.object(mod, "httpx") as mock_httpx, \
         patch.object(mod, "time"):
        mock_httpx.get.return_value = mock_resp
        mock_httpx.HTTPError = Exception

        source = RedditSource()
        mentions = source.fetch_mentions("mellea", since)

    urls = [m.url for m in mentions]
    assert len(urls) == len(set(urls)), "Duplicate URLs found"


def test_reddit_empty_response():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": {"children": []}}
    mock_resp.raise_for_status = MagicMock()

    import core.mention_sources.reddit as mod

    with patch.object(mod, "httpx") as mock_httpx, \
         patch.object(mod, "time"):
        mock_httpx.get.return_value = mock_resp
        mock_httpx.HTTPError = Exception

        source = RedditSource()
        mentions = source.fetch_mentions("mellea", since)

    assert mentions == []

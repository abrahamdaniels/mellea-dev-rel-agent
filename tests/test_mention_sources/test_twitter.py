from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import core.mention_sources.twitter as mod
from core.mention_sources.twitter import TwitterSource

SAMPLE_TWITTER_RESPONSE = {
    "data": [
        {
            "id": "1234567890",
            "text": "Just tried Mellea for structured LLM output — really impressed!",
            "created_at": "2024-04-05T12:00:00Z",
            "author_id": "9876543210",
            "public_metrics": {
                "like_count": 15,
                "retweet_count": 3,
                "reply_count": 2,
            },
        },
        {
            "id": "1234567891",
            "text": "Mellea's streaming validation is a game changer.",
            "created_at": "2024-04-04T08:30:00Z",
            "author_id": "1111111111",
            "public_metrics": {
                "like_count": 8,
                "retweet_count": 1,
                "reply_count": 0,
            },
        },
    ],
}


def test_twitter_parses_tweets():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_TWITTER_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch.object(mod, "httpx") as mock_httpx, \
         patch.object(mod, "get_config") as mock_cfg:
        mock_httpx.get.return_value = mock_resp
        mock_httpx.HTTPError = Exception
        mock_cfg.return_value = MagicMock(twitter_bearer_token="fake-token")

        source = TwitterSource()
        mentions = source.fetch_mentions("mellea", since)

    assert len(mentions) == 2
    assert mentions[0].source == "twitter"
    assert "twitter.com" in mentions[0].url
    assert mentions[0].score == 15


def test_twitter_is_available_false_without_token():
    with patch.object(mod, "get_config") as mock_cfg:
        mock_cfg.return_value = MagicMock(twitter_bearer_token="")
        source = TwitterSource()
        assert source.is_available() is False


def test_twitter_is_available_true_with_token():
    with patch.object(mod, "get_config") as mock_cfg:
        mock_cfg.return_value = MagicMock(twitter_bearer_token="AAA_bearer_token")
        source = TwitterSource()
        assert source.is_available() is True

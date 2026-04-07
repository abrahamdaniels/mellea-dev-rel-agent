from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import core.mention_sources.hackernews as mod
from core.mention_sources.hackernews import HackerNewsSource

SAMPLE_HN_STORIES = {
    "hits": [
        {
            "title": "Mellea: Structured LLM Output",
            "story_text": "A new library for reliable LLM generation.",
            "url": "https://example.com/mellea",
            "author": "hn_poster",
            "created_at_i": 1712400000,
            "points": 150,
            "objectID": "111",
            "num_comments": 30,
        }
    ]
}

SAMPLE_HN_COMMENTS = {
    "hits": [
        {
            "story_title": "Mellea: Structured LLM Output",
            "comment_text": "This looks promising, will try it.",
            "author": "commenter",
            "created_at_i": 1712410000,
            "points": None,
            "objectID": "222",
            "num_comments": None,
        }
    ]
}


def test_hackernews_parses_stories_and_comments():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    call_count = [0]

    def _mock_get(*args, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if call_count[0] == 0:
            resp.json.return_value = SAMPLE_HN_STORIES
        else:
            resp.json.return_value = SAMPLE_HN_COMMENTS
        call_count[0] += 1
        return resp

    with patch.object(mod, "httpx") as mock_httpx:
        mock_httpx.get.side_effect = _mock_get
        mock_httpx.HTTPError = Exception

        source = HackerNewsSource()
        mentions = source.fetch_mentions("mellea", since)

    assert len(mentions) == 2
    story = [m for m in mentions if m.metadata.get("type") == "story"]
    assert len(story) == 1
    assert story[0].title == "Mellea: Structured LLM Output"
    assert story[0].score == 150

    comment = [m for m in mentions if m.metadata.get("type") == "comment"]
    assert len(comment) == 1
    assert comment[0].title == "Mellea: Structured LLM Output"


def test_hackernews_empty_response():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"hits": []}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(mod, "httpx") as mock_httpx:
        mock_httpx.get.return_value = mock_resp
        mock_httpx.HTTPError = Exception

        source = HackerNewsSource()
        mentions = source.fetch_mentions("mellea", since)

    assert mentions == []

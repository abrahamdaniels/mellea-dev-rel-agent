from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import core.mention_sources.stackoverflow as mod
from core.mention_sources.stackoverflow import StackOverflowSource

SAMPLE_SO_RESPONSE = {
    "items": [
        {
            "title": "How to use Mellea for structured output?",
            "excerpt": "I'm trying to use Mellea to validate LLM responses...",
            "question_id": 78901234,
            "item_type": "question",
            "creation_date": 1712400000,
            "score": 5,
            "tags": ["python", "llm", "mellea"],
            "has_accepted_answer": True,
        },
        {
            "title": "Mellea streaming validation",
            "excerpt": "You can use session.instruct with stream=True...",
            "question_id": 78901234,
            "answer_id": 78905678,
            "item_type": "answer",
            "creation_date": 1712410000,
            "score": 3,
            "tags": ["python", "mellea"],
            "has_accepted_answer": True,
        },
    ],
    "has_more": False,
    "quota_remaining": 290,
}


def test_stackoverflow_parses_questions_and_answers():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_SO_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch.object(mod, "httpx") as mock_httpx:
        mock_httpx.get.return_value = mock_resp
        mock_httpx.HTTPError = Exception

        source = StackOverflowSource()
        mentions = source.fetch_mentions("mellea", since)

    assert len(mentions) == 2
    questions = [m for m in mentions if m.metadata.get("item_type") == "question"]
    assert len(questions) == 1
    assert questions[0].title == "How to use Mellea for structured output?"
    assert "stackoverflow.com/q/" in questions[0].url

    answers = [m for m in mentions if m.metadata.get("item_type") == "answer"]
    assert len(answers) == 1
    assert "stackoverflow.com/a/" in answers[0].url


def test_stackoverflow_empty_response():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"items": [], "has_more": False}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(mod, "httpx") as mock_httpx:
        mock_httpx.get.return_value = mock_resp
        mock_httpx.HTTPError = Exception

        source = StackOverflowSource()
        mentions = source.fetch_mentions("mellea", since)

    assert mentions == []


def test_stackoverflow_handles_http_error():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)

    with patch.object(mod, "httpx") as mock_httpx:
        mock_httpx.get.side_effect = Exception("Connection error")
        mock_httpx.HTTPError = Exception

        source = StackOverflowSource()
        mentions = source.fetch_mentions("mellea", since)

    assert mentions == []

from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import Mention, SentimentResult

SAMPLE_MENTIONS = [
    Mention(
        source="reddit",
        title="Mellea question",
        content="How does mellea compare to guardrails?",
        url="https://reddit.com/r/test/1",
        author="user1",
        timestamp="2024-04-05T10:00:00+00:00",
        score=5,
    ),
    Mention(
        source="reddit",
        title="Low score post",
        content="mellea in a list",
        url="https://reddit.com/r/test/2",
        author="user2",
        timestamp="2024-04-04T10:00:00+00:00",
        score=1,
    ),
]


def _make_mock_llm():
    mock = MagicMock()
    mock.generate_structured.return_value = SentimentResult(sentiment="neutral")
    return mock


def _mock_source(mentions):
    source = MagicMock()
    source.fetch_mentions.return_value = mentions
    return source


def test_mentions_classifies_sentiment():
    mock_llm = _make_mock_llm()

    with patch("agents.monitor.mentions.LLMClient", return_value=mock_llm), \
         patch("agents.monitor.mentions.get_source") as mock_get_source, \
         patch("agents.monitor.mentions.save_brief"), \
         patch("agents.monitor.mentions.get_config") as mock_cfg:

        mock_cfg.return_value.monitor_mention_sources = ["reddit"]
        mock_cfg.return_value.monitor_keyword = "mellea"
        mock_cfg.return_value.monitor_mention_lookback_days = 7

        mock_get_source.return_value = _mock_source(list(SAMPLE_MENTIONS))

        from agents.monitor.mentions import run

        run(sources=["reddit"])

    # Sentiment classification called for each mention
    assert mock_llm.generate_structured.call_count == 2


def test_mentions_filters_low_score():
    mock_llm = _make_mock_llm()

    with patch("agents.monitor.mentions.LLMClient", return_value=mock_llm), \
         patch("agents.monitor.mentions.get_source") as mock_get_source, \
         patch("agents.monitor.mentions.save_brief"), \
         patch("agents.monitor.mentions.get_config") as mock_cfg:

        mock_cfg.return_value.monitor_mention_sources = ["reddit"]
        mock_cfg.return_value.monitor_keyword = "mellea"
        mock_cfg.return_value.monitor_mention_lookback_days = 7

        mock_get_source.return_value = _mock_source(list(SAMPLE_MENTIONS))

        from agents.monitor.mentions import run

        result = run(sources=["reddit"])

    # Score 1 should be filtered out
    assert len(result) == 1
    assert result[0].score == 5


def test_mentions_source_filter():
    mock_llm = _make_mock_llm()

    with patch("agents.monitor.mentions.LLMClient", return_value=mock_llm), \
         patch("agents.monitor.mentions.get_source") as mock_get_source, \
         patch("agents.monitor.mentions.save_brief"), \
         patch("agents.monitor.mentions.get_config") as mock_cfg:

        mock_cfg.return_value.monitor_mention_sources = ["reddit", "hackernews"]
        mock_cfg.return_value.monitor_keyword = "mellea"
        mock_cfg.return_value.monitor_mention_lookback_days = 7

        mock_get_source.return_value = _mock_source([])

        from agents.monitor.mentions import run

        run(sources=["reddit"])

    # Only reddit should be queried
    mock_get_source.assert_called_once_with("reddit")


def test_mentions_saves_brief():
    mock_llm = _make_mock_llm()

    with patch("agents.monitor.mentions.LLMClient", return_value=mock_llm), \
         patch("agents.monitor.mentions.get_source") as mock_get_source, \
         patch("agents.monitor.mentions.save_brief") as mock_brief, \
         patch("agents.monitor.mentions.get_config") as mock_cfg:

        mock_cfg.return_value.monitor_mention_sources = ["reddit"]
        mock_cfg.return_value.monitor_keyword = "mellea"
        mock_cfg.return_value.monitor_mention_lookback_days = 7

        mock_get_source.return_value = _mock_source([SAMPLE_MENTIONS[0]])

        from agents.monitor.mentions import run

        run(sources=["reddit"])

    mock_brief.assert_called_once()
    assert mock_brief.call_args[0][0] == "mentions"

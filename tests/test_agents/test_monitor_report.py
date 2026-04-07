from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import DraftOutput, Mention, SentimentResult

SAMPLE_MENTIONS = [
    Mention(
        source="reddit",
        title="Mellea is useful",
        content="Used it for structured output.",
        url="https://reddit.com/r/test/1",
        author="user1",
        timestamp="2024-04-05T10:00:00+00:00",
        score=25,
    ),
    Mention(
        source="hackernews",
        title="Show HN: Mellea",
        content="New library for LLM reliability.",
        url="https://news.ycombinator.com/item?id=1",
        author="user2",
        timestamp="2024-04-04T10:00:00+00:00",
        score=100,
    ),
]


def _make_mock_llm():
    mock = MagicMock()
    mock.generate_with_template.return_value = (
        "# Weekly Report\n## Metrics Snapshot\nStars: 100\n"
        "## Mention Activity\n| Source | Count |\n"
        "## Publication Activity\nNone\n"
        "## Highlights and Recommendations\n- Write about streaming"
    )
    mock.generate_structured.return_value = SentimentResult(sentiment="positive")
    return mock


def test_report_loads_correct_skills():
    from agents.monitor.report import SKILL_MANIFEST
    from core.skill_loader import resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, flags={})
    names = [p.stem for p in paths]
    assert "weekly-report" in names
    assert "sentiment-scoring" in names


def test_report_generates_with_mentions():
    mock_llm = _make_mock_llm()

    with patch("agents.monitor.report.LLMClient", return_value=mock_llm), \
         patch("agents.monitor.report._fetch_github_stats", return_value={"stars": 100}), \
         patch("agents.monitor.report._fetch_pypi_stats",
               return_value={"downloads_last_week": 500}), \
         patch("agents.monitor.report._fetch_mentions", return_value=list(SAMPLE_MENTIONS)), \
         patch("agents.monitor.report.save_draft") as mock_save, \
         patch("agents.monitor.report.save_brief") as mock_brief:

        mock_save.return_value = DraftOutput(
            agent_name="monitor-report", content="report", file_path="drafts/report.md"
        )

        from agents.monitor.report import run

        result = run(sources=["reddit", "hackernews"], stdout_only=True)

    assert result.agent_name == "monitor-report"
    # Sentiment classification should be called for each mention
    assert mock_llm.generate_structured.call_count == 2
    # Brief should be saved
    mock_brief.assert_called_once()
    brief_args = mock_brief.call_args
    assert brief_args[0][0] == "weekly-report"


def test_report_source_filter():
    mock_llm = _make_mock_llm()

    with patch("agents.monitor.report.LLMClient", return_value=mock_llm), \
         patch("agents.monitor.report._fetch_github_stats", return_value={}), \
         patch("agents.monitor.report._fetch_pypi_stats", return_value={}), \
         patch("agents.monitor.report._fetch_mentions") as mock_fetch, \
         patch("agents.monitor.report.save_draft") as mock_save, \
         patch("agents.monitor.report.save_brief"):

        mock_fetch.return_value = []
        mock_save.return_value = DraftOutput(
            agent_name="monitor-report", content="", file_path=None
        )

        from agents.monitor.report import run

        run(sources=["reddit"])

    mock_fetch.assert_called_once()
    call_args = mock_fetch.call_args
    assert call_args[0][0] == ["reddit"]


def test_report_empty_mentions():
    mock_llm = _make_mock_llm()

    with patch("agents.monitor.report.LLMClient", return_value=mock_llm), \
         patch("agents.monitor.report._fetch_github_stats", return_value={}), \
         patch("agents.monitor.report._fetch_pypi_stats", return_value={}), \
         patch("agents.monitor.report._fetch_mentions", return_value=[]), \
         patch("agents.monitor.report.save_draft") as mock_save, \
         patch("agents.monitor.report.save_brief"):

        mock_save.return_value = DraftOutput(
            agent_name="monitor-report", content="empty", file_path=None
        )

        from agents.monitor.report import run

        result = run()

    # Should not error on empty mentions
    assert result is not None
    # No sentiment calls needed
    assert mock_llm.generate_structured.call_count == 0

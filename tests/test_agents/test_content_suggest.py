from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import DraftOutput

SAMPLE_SUGGESTIONS = """# Content Suggestions - 2024-04-06

## Top Opportunities

### 1. Streaming API benchmarks
**Why now:** Reddit mentions of streaming grew 3x this week
**Recommended format:** technical_blog
**Recommended tone:** personal
**Context to use:** `brief:weekly-report`

### 2. Getting started with Mellea
**Why now:** Multiple community questions about onboarding
**Recommended format:** social_post
**Recommended tone:** ibm
**Context to use:** `https://github.com/generative-computing/mellea`
"""


def _make_mock_llm():
    mock = MagicMock()
    mock.generate_with_template.return_value = SAMPLE_SUGGESTIONS
    return mock


def test_suggest_loads_skills():
    from agents.content.suggest import SKILL_MANIFEST
    from core.skill_loader import resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, flags={})
    names = [p.stem for p in paths]
    assert "suggest" in names
    assert "mellea-knowledge" in names


def test_suggest_calls_llm_with_template():
    mock_llm = _make_mock_llm()

    with patch("agents.content.suggest.LLMClient", return_value=mock_llm), \
         patch("agents.content.suggest.load_brief", side_effect=FileNotFoundError("no brief")), \
         patch("agents.content.suggest._fetch_recent_github_activity", return_value="No data"), \
         patch("agents.content.suggest.save_draft") as mock_save:

        mock_save.return_value = DraftOutput(
            agent_name="content-suggest", content=SAMPLE_SUGGESTIONS, file_path=None
        )

        from agents.content.suggest import run

        result = run(stdout_only=True)

    assert result.agent_name == "content-suggest"
    mock_llm.generate_with_template.assert_called_once()
    call_args = mock_llm.generate_with_template.call_args
    assert call_args[0][0] == "content/suggest"


def test_suggest_handles_missing_briefs():
    mock_llm = _make_mock_llm()

    with patch("agents.content.suggest.LLMClient", return_value=mock_llm), \
         patch("agents.content.suggest.load_brief", side_effect=FileNotFoundError("no brief")), \
         patch("agents.content.suggest._fetch_recent_github_activity", return_value="No data"), \
         patch("agents.content.suggest.save_draft") as mock_save:

        mock_save.return_value = DraftOutput(
            agent_name="content-suggest", content="suggestions", file_path=None
        )

        from agents.content.suggest import run

        # Should not raise when briefs are missing
        result = run(stdout_only=True)

    assert result is not None


def test_suggest_merges_additional_context():
    mock_llm = _make_mock_llm()
    mock_context = MagicMock()
    mock_context.combined_text = "Additional info about streaming API"

    with patch("agents.content.suggest.LLMClient", return_value=mock_llm), \
         patch("agents.content.suggest.load_brief", side_effect=FileNotFoundError), \
         patch("agents.content.suggest._fetch_recent_github_activity", return_value="No data"), \
         patch("agents.content.suggest.resolve_context",
               return_value=mock_context) as mock_resolve, \
         patch("agents.content.suggest.save_draft") as mock_save:

        mock_save.return_value = DraftOutput(
            agent_name="content-suggest", content="suggestions", file_path=None
        )

        from agents.content.suggest import run

        run(context_inputs=["streaming API notes"], stdout_only=True)

    mock_resolve.assert_called_once()
    # Additional context should be passed to template
    template_vars = mock_llm.generate_with_template.call_args[0][1]
    assert "Additional info" in template_vars["additional_context"]

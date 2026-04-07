from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import DraftOutput

SAMPLE_CONCEPTS = """# Demo Concepts

## Concept 1: Structured Output
**Description:** A demo using Mellea structured output.
**Target audience:** ML engineers
**Complexity:** S
**Mellea features:** @generative, structured output
**Why this works:** Shows the simplest Mellea use case.
"""


def _make_mock_llm():
    mock = MagicMock()
    mock.generate_with_template.return_value = SAMPLE_CONCEPTS
    return mock


def test_ideation_calls_template():
    mock_llm = _make_mock_llm()

    with patch("agents.demo.ideation.LLMClient", return_value=mock_llm), \
         patch("agents.demo.ideation.resolve_context") as mock_ctx, \
         patch("agents.demo.ideation.load_brief", side_effect=FileNotFoundError), \
         patch("agents.demo.ideation.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(combined_text="Feature X info")
        mock_save.return_value = DraftOutput(
            agent_name="demo-ideation", content=SAMPLE_CONCEPTS, file_path=None
        )

        from agents.demo.ideation import run
        run(context_inputs=["Feature X"])

    mock_llm.generate_with_template.assert_called_once()
    assert mock_llm.generate_with_template.call_args[0][0] == "demo/concept"


def test_ideation_loads_skills():
    from agents.demo.ideation import SKILL_MANIFEST
    from core.skill_loader import resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, flags={})
    names = [p.stem for p in paths]
    assert "ideation" in names
    assert "mellea-knowledge" in names


def test_ideation_without_context():
    mock_llm = _make_mock_llm()

    with patch("agents.demo.ideation.LLMClient", return_value=mock_llm), \
         patch("agents.demo.ideation.load_brief", side_effect=FileNotFoundError), \
         patch("agents.demo.ideation.save_draft") as mock_save:

        mock_save.return_value = DraftOutput(
            agent_name="demo-ideation", content=SAMPLE_CONCEPTS, file_path=None
        )

        from agents.demo.ideation import run
        result = run(context_inputs=None, stdout_only=True)

    assert result.agent_name == "demo-ideation"


def test_ideation_saves_draft():
    mock_llm = _make_mock_llm()

    with patch("agents.demo.ideation.LLMClient", return_value=mock_llm), \
         patch("agents.demo.ideation.load_brief", side_effect=FileNotFoundError), \
         patch("agents.demo.ideation.save_draft") as mock_save:

        mock_save.return_value = DraftOutput(
            agent_name="demo-ideation", content=SAMPLE_CONCEPTS, file_path="drafts/x.md"
        )

        from agents.demo.ideation import run
        run(stdout_only=False)

    mock_save.assert_called_once()
    assert mock_save.call_args.kwargs.get("agent_name") == "demo-ideation" or \
           mock_save.call_args[1].get("agent_name") == "demo-ideation" or \
           mock_save.call_args[0][0] == "demo-ideation"

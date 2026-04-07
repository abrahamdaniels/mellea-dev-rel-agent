"""Tests for the Blog Outline agent."""
from unittest.mock import MagicMock, patch

from core.models import DraftOutput

SAMPLE_OUTLINE = """# Blog Outline: Streaming Validation in Mellea

**Target audience:** Python developers building LLM apps that need real-time validation
**Suggested length:** 800-1000 words
**Key Mellea features:** session.instruct(stream=True), StreamValidator

## Title Options
1. Streaming Validation in Mellea: Catching Errors Before They Finish
2. Real-Time Output Validation with Mellea's Streaming API
3. How Mellea Validates LLM Output Token-by-Token

## What It Is
- Mellea's streaming validation lets you validate structured output as tokens arrive
- Solves the problem of waiting for a full response before discovering schema violations
- Builds on Mellea's core validation engine, extending it to streaming contexts

## Why It Matters
- Without streaming validation, you waste compute on responses that fail validation at the end
- Reduces p95 latency for structured output pipelines by catching failures early
- No other Python library offers token-level schema validation during streaming

## How To Use It
- Install: `pip install mellea`
- Call `session.instruct("prompt", stream=True, validate=True)`
- Each chunk is validated incrementally; a `ValidationError` is raised on first violation
"""


def test_outline_has_required_sections():
    """Outline must have the three required IBM Research sections."""
    for section in ["What It Is", "Why It Matters", "How To Use It"]:
        assert section in SAMPLE_OUTLINE


def test_outline_has_title_options():
    """Outline must include title suggestions."""
    assert "Title Options" in SAMPLE_OUTLINE


def test_agent_run_calls_template(tmp_path):
    with patch("agents.content.blog_outline.LLMClient") as MockLLM, \
         patch("agents.content.blog_outline.resolve_context") as mock_ctx, \
         patch("agents.content.blog_outline.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(
            combined_text="PR adds streaming validation.",
            sources=[MagicMock()],
        )
        MockLLM.return_value.generate_with_template.return_value = SAMPLE_OUTLINE
        mock_save.return_value = DraftOutput(
            agent_name="blog-outline",
            content=SAMPLE_OUTLINE,
            file_path=str(tmp_path / "outline.md"),
            metadata={"context_sources": 1},
        )

        from agents.content.blog_outline import run
        output = run(["https://github.com/generative-computing/mellea/pull/700"])

    assert output.agent_name == "blog-outline"
    MockLLM.return_value.generate_with_template.assert_called_once()
    call_args = MockLLM.return_value.generate_with_template.call_args
    assert call_args[0][0] == "content/blog_outline"


def test_skill_manifest_loads():
    from agents.content.blog_outline import SKILL_MANIFEST
    from core.skill_loader import load_skill_content, resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, flags={})
    names = [p.name for p in paths]
    assert "blog-outline.md" in names
    assert "mellea-knowledge.md" in names

    content = load_skill_content(paths)
    assert "IBM Research" in content
    assert "Mellea" in content


def test_no_post_processing():
    from agents.content.blog_outline import SKILL_MANIFEST
    assert SKILL_MANIFEST["post_processing"] == []

"""Integration tests for the Technical Blog agent."""
from unittest.mock import MagicMock, patch

from core.models import DraftOutput

SAMPLE_BLOG = """---
title: "Streaming Output in Mellea"
thumbnail: /blog/assets/streaming/thumbnail.png
authors:
  - user: testuser
---

Mellea now supports streaming output across all backends.

## The Problem

LLMs generate tokens incrementally but most libraries buffer the full output before returning it.

## How Streaming Works

Pass `stream=True` to `session.instruct()`:

```python
from mellea import start_session

with start_session(backend="ollama", model="granite-3.3-8b") as session:
    for chunk in session.instruct("Explain streaming", stream=True):
        print(chunk, end="", flush=True)
# Output: Streaming output token by token...
```

## Limitations

Streaming is not compatible with structured output validation in the current release.

## Get Started

```bash
pip install mellea
```

GitHub: https://github.com/generative-computing/mellea
"""


def test_blog_structure_has_required_sections():
    """Verify a generated blog has all required sections."""
    assert "## " in SAMPLE_BLOG  # has headings
    # Required sections
    for section_hint in ["Problem", "Works", "Limitations", "Started"]:
        assert section_hint in SAMPLE_BLOG


def test_code_blocks_have_language_tags():
    """Opening fenced code blocks must declare a language (closing ``` lines are ignored)."""
    in_block = False
    for line in SAMPLE_BLOG.splitlines():
        stripped = line.strip()
        if not stripped.startswith("```"):
            continue
        rest = stripped[3:].strip()
        if not in_block:
            assert rest, "Opening fence must include a language tag (e.g. ```python)"
            in_block = True
        else:
            in_block = False


def test_frontmatter_present():
    assert SAMPLE_BLOG.startswith("---\n")
    assert "title:" in SAMPLE_BLOG
    assert "authors:" in SAMPLE_BLOG


def test_cta_has_pip_install():
    assert "pip install mellea" in SAMPLE_BLOG


def test_agent_run_calls_llm_with_template(tmp_path):
    with patch("agents.content.technical_blog.LLMClient") as MockLLM, \
         patch("agents.content.technical_blog.resolve_context") as mock_ctx, \
         patch("agents.content.technical_blog.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(
            combined_text="PR adds streaming to Mellea.",
            sources=[MagicMock()],
        )
        MockLLM.return_value.generate_with_template.return_value = SAMPLE_BLOG
        mock_save.return_value = DraftOutput(
            agent_name="technical-blog",
            content=SAMPLE_BLOG,
            file_path=str(tmp_path / "blog.md"),
            metadata={"context_sources": 1},
        )

        from agents.content.technical_blog import run
        output = run(["https://github.com/generative-computing/mellea/pull/676"])

    assert output.agent_name == "technical-blog"
    MockLLM.return_value.generate_with_template.assert_called_once()
    call_kwargs = MockLLM.return_value.generate_with_template.call_args
    assert call_kwargs[0][0] == "content/technical_blog"


def test_skill_manifest_loads_all_required_skills():
    from agents.content.technical_blog import SKILL_MANIFEST
    from core.skill_loader import load_skill_content, resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, flags={})
    names = [p.name for p in paths]
    assert "technical-blog.md" in names
    assert "mellea-knowledge.md" in names

    content = load_skill_content(paths)
    assert "HuggingFace" in content  # technical-blog skill loaded
    assert "Mellea" in content  # mellea-knowledge loaded


def test_de_llmify_applied_to_output():
    """Verify de-llmify post-processing skill is loaded for the blog agent."""
    from agents.content.technical_blog import SKILL_MANIFEST
    from core.skill_loader import load_skill_content, resolve_post_processing

    pp_paths = resolve_post_processing(SKILL_MANIFEST)
    content = load_skill_content(pp_paths)
    assert "Tier 1" in content  # de-llmify content present

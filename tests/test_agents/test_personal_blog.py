"""Tests for the Personal Blog agent."""
from unittest.mock import MagicMock, patch

from core.models import DraftOutput

SAMPLE_BLOG = """# I Replaced My Validation Pipeline With One Mellea Call

Last week I was debugging a chain of three Pydantic validators stapled together
with try/except blocks. It worked, mostly, but every edge case meant another
branch. I ripped it out and replaced it with Mellea's `session.instruct()` and
a single schema. Here's what happened.

## The Setup

I had a FastAPI endpoint that took user prompts, sent them to GPT-4, and
validated the response against a Pydantic model. The validation code was 80
lines of defensive programming.

```python
from mellea import start_session

with start_session(backend="ollama", model="granite-3.3-8b") as session:
    result = session.instruct(
        "Generate a product review with title, rating, and body",
        output_schema=ProductReview,
    )
    print(result.title, result.rating)
```

## What Surprised Me

The retry logic is built in. When the LLM output doesn't match the schema,
Mellea re-prompts automatically. I didn't have to write any of that.

## What I'd Do Differently

I'd start with streaming validation next time — I only discovered it after
I'd already shipped the non-streaming version.

Try it: `pip install mellea` — the README has a 5-minute quickstart.
"""


def test_blog_has_first_person():
    """Personal blog must use first-person voice."""
    assert " I " in SAMPLE_BLOG


def test_blog_has_honest_opinion():
    """Personal blog should contain a personal judgment or opinion."""
    assert "Surprised" in SAMPLE_BLOG or "I think" in SAMPLE_BLOG


def test_agent_run_calls_template(tmp_path):
    with patch("agents.content.personal_blog.LLMClient") as MockLLM, \
         patch("agents.content.personal_blog.resolve_context") as mock_ctx, \
         patch("agents.content.personal_blog.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(
            combined_text="PR adds structured output validation.",
            sources=[MagicMock()],
        )
        MockLLM.return_value.generate_with_template.return_value = SAMPLE_BLOG
        mock_save.return_value = DraftOutput(
            agent_name="personal-blog",
            content=SAMPLE_BLOG,
            file_path=str(tmp_path / "blog.md"),
            metadata={"context_sources": 1},
        )

        from agents.content.personal_blog import run
        output = run(["https://github.com/generative-computing/mellea/pull/700"])

    assert output.agent_name == "personal-blog"
    MockLLM.return_value.generate_with_template.assert_called_once()
    call_args = MockLLM.return_value.generate_with_template.call_args
    assert call_args[0][0] == "content/personal_blog"


def test_skill_manifest_loads():
    from agents.content.personal_blog import SKILL_MANIFEST
    from core.skill_loader import load_skill_content, resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, flags={})
    names = [p.name for p in paths]
    assert "personal-blog.md" in names
    assert "mellea-knowledge.md" in names

    content = load_skill_content(paths)
    assert "conversational" in content.lower()
    assert "Mellea" in content


def test_de_llmify_in_post_processing():
    from agents.content.personal_blog import SKILL_MANIFEST
    from core.skill_loader import load_skill_content, resolve_post_processing

    pp_paths = resolve_post_processing(SKILL_MANIFEST)
    content = load_skill_content(pp_paths)
    assert "Tier 1" in content

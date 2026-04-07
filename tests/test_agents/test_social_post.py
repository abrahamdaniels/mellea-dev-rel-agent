"""Integration tests for the Social Post agent."""
from unittest.mock import MagicMock, patch

from core.models import DraftOutput

# ---- Helpers ----

def _make_mock_llm(response: str = "Mock post content"):
    mock = MagicMock()
    mock.generate_with_template.return_value = response
    return mock


# ---- Tests ----

def test_personal_tone_twitter_produces_draft(tmp_path):
    with patch("agents.content.social_post.LLMClient") as MockLLM, \
         patch("agents.content.social_post.resolve_context") as mock_ctx, \
         patch("agents.content.social_post.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(combined_text="PR adds streaming support to Mellea.")
        MockLLM.return_value = _make_mock_llm("Mellea now streams. 3 lines of code. github.com/x")
        mock_save.return_value = DraftOutput(
            agent_name="social-post-twitter",
            content="Mellea now streams. 3 lines of code. github.com/x",
            file_path=str(tmp_path / "draft.md"),
            metadata={"platform": "twitter", "tone": "personal"},
        )

        from agents.content.social_post import run
        outputs = run(["streaming feature"], tone="personal", platform="twitter")

    assert len(outputs) == 1
    assert outputs[0].metadata["platform"] == "twitter"
    assert outputs[0].metadata["tone"] == "personal"


def test_ibm_tone_linkedin_produces_draft(tmp_path):
    with patch("agents.content.social_post.LLMClient") as MockLLM, \
         patch("agents.content.social_post.resolve_context") as mock_ctx, \
         patch("agents.content.social_post.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(combined_text="IBM Research introduces streaming.")
        MockLLM.return_value = _make_mock_llm(
            "IBM Research has introduced streaming support in Mellea.",
        )
        mock_save.return_value = DraftOutput(
            agent_name="social-post-linkedin",
            content="IBM Research has introduced streaming support in Mellea.",
            file_path=str(tmp_path / "draft.md"),
            metadata={"platform": "linkedin", "tone": "ibm"},
        )

        from agents.content.social_post import run
        outputs = run(["streaming feature"], tone="ibm", platform="linkedin")

    assert len(outputs) == 1
    assert outputs[0].metadata["platform"] == "linkedin"
    assert outputs[0].metadata["tone"] == "ibm"


def test_both_platforms_produces_two_drafts(tmp_path):
    with patch("agents.content.social_post.LLMClient") as MockLLM, \
         patch("agents.content.social_post.resolve_context") as mock_ctx, \
         patch("agents.content.social_post.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(combined_text="New feature context.")
        MockLLM.return_value = _make_mock_llm("Draft content")

        call_count = [0]

        def mock_save_side_effect(agent_name, content, metadata, stdout_only):
            call_count[0] += 1
            return DraftOutput(agent_name=agent_name, content=content, metadata=metadata)

        mock_save.side_effect = mock_save_side_effect

        from agents.content.social_post import run
        outputs = run(["context"], tone="personal", platform="both")

    assert len(outputs) == 2
    platforms = {o.metadata["platform"] for o in outputs}
    assert platforms == {"twitter", "linkedin"}


def test_skill_manifest_loads_correct_skills():
    """Verify skill manifest resolves without error using real skill files."""
    from agents.content.social_post import SKILL_MANIFEST
    from core.skill_loader import resolve_manifest

    # personal + twitter
    paths = resolve_manifest(SKILL_MANIFEST, {"tone": "personal", "platform": "twitter"})
    names = [p.name for p in paths]
    assert "social-post.md" in names
    assert "mellea-knowledge.md" in names
    assert "tone-personal.md" in names
    assert "twitter-conventions.md" in names
    assert "tone-ibm.md" not in names
    assert "linkedin-conventions.md" not in names


def test_skill_manifest_ibm_linkedin():
    from agents.content.social_post import SKILL_MANIFEST
    from core.skill_loader import resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, {"tone": "ibm", "platform": "linkedin"})
    names = [p.name for p in paths]
    assert "tone-ibm.md" in names
    assert "linkedin-conventions.md" in names
    assert "tone-personal.md" not in names
    assert "twitter-conventions.md" not in names


def test_context_from_raw_text():
    from core.context_resolver import resolve_context
    block = resolve_context(["New streaming API is available"], no_cache=True)
    assert "New streaming API" in block.combined_text


def test_context_from_mixed_inputs(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("Streaming notes.")
    from core.context_resolver import resolve_context
    block = resolve_context([str(f), "Free text about feature"], no_cache=True)
    assert len(block.sources) == 2
    assert "Streaming notes" in block.combined_text
    assert "Free text about feature" in block.combined_text


def test_de_llmify_skill_loads():
    """Verify the de-llmify post-processing skill file loads cleanly."""
    from agents.content.social_post import SKILL_MANIFEST
    from core.skill_loader import load_skill_content, resolve_post_processing

    pp_paths = resolve_post_processing(SKILL_MANIFEST)
    content = load_skill_content(pp_paths)
    assert "Tier 1" in content  # de-llmify skill content is present
    assert "name: de-llmify" not in content  # frontmatter was stripped

"""Tests for core/skill_loader.py"""
from pathlib import Path

import pytest

from core.skill_loader import load_skill_content, resolve_manifest, resolve_post_processing

MANIFEST = {
    "always": ["content/social-post"],
    "conditional": {
        "tone": {
            "personal": "shared/tone-personal",
            "ibm": "shared/tone-ibm",
        },
        "platform": {
            "twitter": "content/twitter-conventions",
        },
    },
    "post_processing": ["content/de-llmify"],
}


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory with stub skill files."""
    content_dir = tmp_path / "content"
    shared_dir = tmp_path / "shared"
    content_dir.mkdir()
    shared_dir.mkdir()

    (content_dir / "social-post.md").write_text(
        "---\nname: social-post\n---\n\n# Social Post\nPost instructions here."
    )
    (shared_dir / "tone-personal.md").write_text(
        "---\nname: tone-personal\n---\n\n# Personal Tone\nBe casual."
    )
    (shared_dir / "tone-ibm.md").write_text(
        "---\nname: tone-ibm\n---\n\n# IBM Tone\nBe professional."
    )
    (content_dir / "twitter-conventions.md").write_text(
        "---\nname: twitter-conventions\n---\n\n# Twitter\n280 chars max."
    )
    (content_dir / "de-llmify.md").write_text(
        "---\nname: de-llmify\n---\n\n# De-LLMify\nRemove AI tells."
    )
    return tmp_path


def test_always_skills_always_load(skills_dir):
    paths = resolve_manifest(MANIFEST, flags={}, skills_dir=skills_dir)
    names = [p.stem for p in paths]
    assert "social-post" in names


def test_conditional_personal_tone(skills_dir):
    paths = resolve_manifest(MANIFEST, {"tone": "personal"}, skills_dir=skills_dir)
    names = [p.name for p in paths]
    assert "tone-personal.md" in names
    assert "tone-ibm.md" not in names


def test_conditional_ibm_tone(skills_dir):
    paths = resolve_manifest(MANIFEST, {"tone": "ibm"}, skills_dir=skills_dir)
    names = [p.name for p in paths]
    assert "tone-ibm.md" in names
    assert "tone-personal.md" not in names


def test_unmatched_flag_skipped(skills_dir):
    # No "tone" flag at all — conditional tone skills should be skipped
    paths = resolve_manifest(MANIFEST, flags={}, skills_dir=skills_dir)
    names = [p.name for p in paths]
    assert "tone-personal.md" not in names
    assert "tone-ibm.md" not in names


def test_post_processing_returns_separate_list(skills_dir):
    pp_paths = resolve_post_processing(MANIFEST, skills_dir=skills_dir)
    names = [p.name for p in pp_paths]
    assert "de-llmify.md" in names


def test_missing_file_raises_clear_error(skills_dir):
    bad_manifest = {"always": ["content/nonexistent"]}
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        resolve_manifest(bad_manifest, flags={}, skills_dir=skills_dir)


def test_frontmatter_is_stripped(skills_dir):
    paths = resolve_manifest(MANIFEST, {"tone": "personal"}, skills_dir=skills_dir)
    content = load_skill_content(paths)
    assert "name: social-post" not in content
    assert "# Social Post" in content


def test_skills_joined_with_separator(skills_dir):
    paths = resolve_manifest(MANIFEST, {"tone": "personal"}, skills_dir=skills_dir)
    content = load_skill_content(paths)
    assert "---" in content

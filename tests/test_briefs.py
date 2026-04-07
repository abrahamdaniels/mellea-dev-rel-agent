from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from core.config import DevRelConfig


def _config_with_briefs_dir(tmp_path):
    return DevRelConfig(github_token="", briefs_dir=str(tmp_path / "briefs"))


def test_save_and_load_roundtrip(tmp_path):
    config = _config_with_briefs_dir(tmp_path)
    with patch("core.briefs.get_config", return_value=config):
        from core.briefs import load_brief, save_brief

        data = {"mentions": [{"source": "reddit", "title": "test"}], "count": 1}
        path = save_brief("weekly-report", data)

        assert path.exists()
        loaded = load_brief("weekly-report")

    assert loaded["mentions"][0]["source"] == "reddit"
    assert loaded["count"] == 1


def test_load_missing_brief_raises(tmp_path):
    config = _config_with_briefs_dir(tmp_path)
    with patch("core.briefs.get_config", return_value=config):
        from core.briefs import load_brief

        with pytest.raises(FileNotFoundError, match="nonexistent"):
            load_brief("nonexistent")


def test_brief_date_returns_iso_string(tmp_path):
    config = _config_with_briefs_dir(tmp_path)
    with patch("core.briefs.get_config", return_value=config):
        from core.briefs import get_brief_date, save_brief

        save_brief("test-brief", {"data": 1})
        date = get_brief_date("test-brief")

    assert "T" in date  # ISO format has T separator


def test_context_resolver_handles_brief_prefix(tmp_path):
    config = _config_with_briefs_dir(tmp_path)
    brief_data = {"mentions": [{"source": "hackernews"}], "count": 5}
    # Write brief file manually
    briefs_dir = tmp_path / "briefs"
    briefs_dir.mkdir()
    (briefs_dir / "latest-weekly-report.json").write_text(json.dumps(brief_data))

    with patch("core.briefs.get_config", return_value=config):
        from core.context_resolver import _resolve_single

        source = _resolve_single("brief:weekly-report", no_cache=True)

    assert source.source_type == "brief"
    assert source.title == "Brief: weekly-report"
    assert "hackernews" in source.content


def test_brief_content_in_combined_text(tmp_path):
    config = _config_with_briefs_dir(tmp_path)
    briefs_dir = tmp_path / "briefs"
    briefs_dir.mkdir()
    (briefs_dir / "latest-mentions.json").write_text(json.dumps({"data": "test"}))

    with patch("core.briefs.get_config", return_value=config):
        from core.context_resolver import resolve_context

        block = resolve_context(["brief:mentions", "some raw text"], no_cache=True)

    assert "Brief: mentions" in block.combined_text
    assert "some raw text" in block.combined_text
    assert len(block.sources) == 2

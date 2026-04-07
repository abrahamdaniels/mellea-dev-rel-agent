from __future__ import annotations

from unittest.mock import patch

import pytest


def test_all_sources_registered():
    from core.mention_sources.registry import get_all_sources

    sources = get_all_sources()
    names = {s.source_name for s in sources}
    assert "reddit" in names
    assert "hackernews" in names
    assert "github_discussions" in names
    assert "pypi" in names
    assert "stackoverflow" in names
    assert "twitter" in names
    assert "linkedin" in names
    assert len(names) == 7


def test_get_source_returns_correct_type():
    from core.mention_sources.reddit import RedditSource
    from core.mention_sources.registry import get_source

    source = get_source("reddit")
    assert isinstance(source, RedditSource)


def test_get_source_unknown_raises():
    from core.mention_sources.registry import get_source

    with pytest.raises(ValueError, match="Unknown mention source"):
        get_source("nonexistent")


def test_get_available_sources_filters():
    from core.mention_sources.registry import get_available_sources

    # Mock all token-gated sources to have no tokens
    with patch("core.mention_sources.github_discussions.get_config") as mock_gh_cfg, \
         patch("core.mention_sources.twitter.get_config") as mock_tw_cfg, \
         patch("core.mention_sources.linkedin.get_config") as mock_li_cfg:
        mock_gh_cfg.return_value.github_token = ""
        mock_tw_cfg.return_value.twitter_bearer_token = ""
        mock_li_cfg.return_value.linkedin_access_token = ""
        sources = get_available_sources()

    names = {s.source_name for s in sources}
    assert "reddit" in names
    assert "hackernews" in names
    assert "pypi" in names
    assert "stackoverflow" in names
    # Token-gated sources should be filtered out when no tokens
    assert "github_discussions" not in names
    assert "twitter" not in names
    assert "linkedin" not in names

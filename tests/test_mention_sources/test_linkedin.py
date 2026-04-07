from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import core.mention_sources.linkedin as mod
from core.mention_sources.linkedin import LinkedInSource


def test_linkedin_is_available_false_without_token():
    with patch.object(mod, "get_config") as mock_cfg:
        mock_cfg.return_value = MagicMock(linkedin_access_token="")
        source = LinkedInSource()
        assert source.is_available() is False


def test_linkedin_fetch_returns_empty():
    """LinkedIn has no public search API — fetch always returns empty."""
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)

    with patch.object(mod, "get_config") as mock_cfg:
        mock_cfg.return_value = MagicMock(linkedin_access_token="fake-token")
        source = LinkedInSource()
        mentions = source.fetch_mentions("mellea", since)

    assert mentions == []

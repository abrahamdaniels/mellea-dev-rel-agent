from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import core.mention_sources.pypi as mod
from core.mention_sources.pypi import PyPISource


def test_pypi_parses_stats():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)
    stats_resp = MagicMock()
    stats_resp.json.return_value = {
        "data": {"last_day": 100, "last_week": 700, "last_month": 3000}
    }
    stats_resp.raise_for_status = MagicMock()

    info_resp = MagicMock()
    info_resp.json.return_value = {
        "info": {"version": "0.8.0", "summary": "LLM reliability layer"}
    }
    info_resp.raise_for_status = MagicMock()

    def _mock_get(url, **kwargs):
        if "pypistats" in url:
            return stats_resp
        return info_resp

    with patch.object(mod, "httpx") as mock_httpx:
        mock_httpx.get.side_effect = _mock_get
        mock_httpx.HTTPError = Exception

        source = PyPISource()
        mentions = source.fetch_mentions("mellea", since)

    assert len(mentions) == 1
    m = mentions[0]
    assert m.source == "pypi"
    assert m.metadata["downloads_last_week"] == 700
    assert m.metadata["version"] == "0.8.0"
    assert "v0.8.0" in m.title


def test_pypi_handles_not_found():
    since = datetime(2024, 4, 1, tzinfo=timezone.utc)

    with patch.object(mod, "httpx") as mock_httpx:
        mock_httpx.get.side_effect = Exception("404")
        mock_httpx.HTTPError = Exception

        source = PyPISource()
        mentions = source.fetch_mentions("nonexistent-pkg", since)

    assert mentions == []

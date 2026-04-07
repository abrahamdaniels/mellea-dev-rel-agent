from __future__ import annotations

from datetime import datetime, timezone

import httpx

from core.mention_sources import MentionSource
from core.models import Mention

_PYPI_URL = "https://pypi.org/pypi/{package}/json"
_PYPISTATS_URL = "https://pypistats.org/api/packages/{package}/recent"


class PyPISource(MentionSource):
    @property
    def source_name(self) -> str:
        return "pypi"

    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        """Fetch PyPI package stats. Returns a single Mention with stats in metadata."""
        stats = self._fetch_stats(keyword)
        pkg_info = self._fetch_package_info(keyword)

        if not stats and not pkg_info:
            return []

        version = pkg_info.get("version", "unknown") if pkg_info else "unknown"
        summary = pkg_info.get("summary", "") if pkg_info else ""

        downloads = stats or {}
        content_parts = [f"Package: {keyword} (v{version})"]
        if summary:
            content_parts.append(f"Summary: {summary}")
        if downloads:
            content_parts.append(
                f"Downloads — last day: {downloads.get('last_day', 'N/A')}, "
                f"last week: {downloads.get('last_week', 'N/A')}, "
                f"last month: {downloads.get('last_month', 'N/A')}"
            )

        return [
            Mention(
                source="pypi",
                title=f"{keyword} v{version}",
                content="\n".join(content_parts),
                url=f"https://pypi.org/project/{keyword}/",
                author=None,
                timestamp=datetime.now(tz=timezone.utc),
                score=None,
                metadata={
                    "version": version,
                    "downloads_last_day": downloads.get("last_day"),
                    "downloads_last_week": downloads.get("last_week"),
                    "downloads_last_month": downloads.get("last_month"),
                },
            )
        ]

    def _fetch_stats(self, package: str) -> dict | None:
        try:
            resp = httpx.get(
                _PYPISTATS_URL.format(package=package), timeout=15
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
        except httpx.HTTPError:
            return None

    def _fetch_package_info(self, package: str) -> dict | None:
        try:
            resp = httpx.get(_PYPI_URL.format(package=package), timeout=15)
            resp.raise_for_status()
            return resp.json().get("info", {})
        except httpx.HTTPError:
            return None

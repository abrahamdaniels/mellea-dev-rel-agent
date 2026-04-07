from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from core.models import Mention


class MentionSource(ABC):
    """Abstract interface for fetching mentions from a platform."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Platform identifier (e.g., 'reddit', 'hackernews')."""

    @abstractmethod
    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        """Fetch mentions of `keyword` since the given datetime.
        Returns a list of Mention objects, newest first."""

    def is_available(self) -> bool:
        """Check if this source is configured and reachable.
        Returns True by default; override to add checks."""
        return True

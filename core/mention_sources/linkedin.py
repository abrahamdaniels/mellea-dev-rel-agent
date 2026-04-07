from __future__ import annotations

import logging
from datetime import datetime

from core.config import get_config
from core.mention_sources import MentionSource
from core.models import Mention

logger = logging.getLogger(__name__)


class LinkedInSource(MentionSource):
    """LinkedIn mention source.

    LinkedIn does not expose a public search API for mentions.
    This source requires an OAuth access token and is a placeholder
    for future integration when LinkedIn API access is available.
    Set DEVREL_LINKEDIN_ACCESS_TOKEN in the environment or config.
    """

    @property
    def source_name(self) -> str:
        return "linkedin"

    def is_available(self) -> bool:
        config = get_config()
        return bool(config.linkedin_access_token)

    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        config = get_config()
        if not config.linkedin_access_token:
            return []

        logger.info(
            "LinkedIn mention search is not yet implemented — "
            "LinkedIn API does not expose a public search endpoint for mentions."
        )
        return []

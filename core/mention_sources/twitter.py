from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from core.config import get_config
from core.mention_sources import MentionSource
from core.models import Mention

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"


class TwitterSource(MentionSource):
    """Twitter/X mention source.

    Requires a Twitter API v2 Bearer Token (Basic tier or higher).
    Set DEVREL_TWITTER_BEARER_TOKEN in the environment or config.
    """

    @property
    def source_name(self) -> str:
        return "twitter"

    def is_available(self) -> bool:
        config = get_config()
        return bool(config.twitter_bearer_token)

    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        config = get_config()
        if not config.twitter_bearer_token:
            return []

        since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
        headers = {"Authorization": f"Bearer {config.twitter_bearer_token}"}
        params = {
            "query": keyword,
            "start_time": since_str,
            "max_results": "25",
            "tweet.fields": "created_at,author_id,public_metrics",
        }

        try:
            resp = httpx.get(
                _SEARCH_URL, params=params, headers=headers, timeout=15
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Twitter API request failed")
            return []

        data = resp.json().get("data", [])
        if not data:
            return []

        mentions: list[Mention] = []
        for tweet in data:
            tweet_id = tweet.get("id", "")
            created_str = tweet.get("created_at", "")
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                created = datetime.now(tz=timezone.utc)

            metrics = tweet.get("public_metrics", {})
            mentions.append(
                Mention(
                    source="twitter",
                    title=None,
                    content=tweet.get("text", ""),
                    url=f"https://twitter.com/i/status/{tweet_id}",
                    author=tweet.get("author_id"),
                    timestamp=created,
                    score=metrics.get("like_count"),
                    metadata={
                        "tweet_id": tweet_id,
                        "retweet_count": metrics.get("retweet_count", 0),
                        "reply_count": metrics.get("reply_count", 0),
                    },
                )
            )

        mentions.sort(key=lambda m: m.timestamp, reverse=True)
        return mentions

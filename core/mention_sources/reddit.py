from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx

from core.mention_sources import MentionSource
from core.models import Mention

_USER_AGENT = "mellea-devrel-monitor/0.1 (https://github.com/generative-computing/mellea)"
_BASE_URL = "https://www.reddit.com"
_SUBREDDITS = ["MachineLearning", "LocalLLaMA", "Python"]
_RATE_LIMIT_SECONDS = 2


class RedditSource(MentionSource):
    @property
    def source_name(self) -> str:
        return "reddit"

    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        seen_urls: set[str] = set()
        mentions: list[Mention] = []

        # Global search
        mentions.extend(
            self._search(keyword, since, subreddit=None, seen_urls=seen_urls)
        )

        # Subreddit-specific searches
        for sub in _SUBREDDITS:
            time.sleep(_RATE_LIMIT_SECONDS)
            mentions.extend(
                self._search(keyword, since, subreddit=sub, seen_urls=seen_urls)
            )

        # Sort newest first
        mentions.sort(key=lambda m: m.timestamp, reverse=True)
        return mentions

    def _search(
        self,
        keyword: str,
        since: datetime,
        subreddit: str | None,
        seen_urls: set[str],
    ) -> list[Mention]:
        if subreddit:
            url = f"{_BASE_URL}/r/{subreddit}/search.json"
            params = {"q": keyword, "sort": "new", "t": "week", "restrict_sr": "on", "limit": "25"}
        else:
            url = f"{_BASE_URL}/search.json"
            params = {"q": keyword, "sort": "new", "t": "week", "limit": "25"}

        try:
            resp = httpx.get(
                url, params=params, headers={"User-Agent": _USER_AGENT}, timeout=15
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        data = resp.json()
        results: list[Mention] = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            created = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)
            since_aware = since if since.tzinfo else since.replace(tzinfo=timezone.utc)
            if created < since_aware:
                continue

            post_url = f"https://www.reddit.com{post.get('permalink', '')}"
            if post_url in seen_urls:
                continue
            seen_urls.add(post_url)

            body = post.get("selftext", "") or ""
            title = post.get("title", "")
            results.append(
                Mention(
                    source="reddit",
                    title=title,
                    content=f"{title}\n\n{body}".strip() if body else title,
                    url=post_url,
                    author=post.get("author"),
                    timestamp=created,
                    score=post.get("score"),
                    metadata={
                        "subreddit": post.get("subreddit", ""),
                        "num_comments": post.get("num_comments", 0),
                    },
                )
            )
        return results

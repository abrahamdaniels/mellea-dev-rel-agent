from __future__ import annotations

from datetime import datetime, timezone

import httpx

from core.mention_sources import MentionSource
from core.models import Mention

_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HackerNewsSource(MentionSource):
    @property
    def source_name(self) -> str:
        return "hackernews"

    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        since_ts = int(since.replace(tzinfo=timezone.utc).timestamp()
                       if since.tzinfo is None else since.timestamp())
        mentions: list[Mention] = []

        # Fetch stories
        mentions.extend(self._fetch(keyword, since_ts, tags="story"))
        # Fetch comments
        mentions.extend(self._fetch(keyword, since_ts, tags="comment"))

        mentions.sort(key=lambda m: m.timestamp, reverse=True)
        return mentions

    def _fetch(self, keyword: str, since_ts: int, tags: str) -> list[Mention]:
        params = {
            "query": keyword,
            "tags": tags,
            "numericFilters": f"created_at_i>{since_ts}",
            "hitsPerPage": "25",
        }
        try:
            resp = httpx.get(_ALGOLIA_URL, params=params, timeout=15)
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        results: list[Mention] = []
        for hit in resp.json().get("hits", []):
            created = datetime.fromtimestamp(
                hit.get("created_at_i", 0), tz=timezone.utc
            )
            object_id = hit.get("objectID", "")

            if tags == "story":
                title = hit.get("title", "")
                content = title
                if hit.get("story_text"):
                    content = f"{title}\n\n{hit['story_text']}"
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            else:
                title = hit.get("story_title", "")
                content = hit.get("comment_text", "")
                url = f"https://news.ycombinator.com/item?id={object_id}"

            results.append(
                Mention(
                    source="hackernews",
                    title=title,
                    content=content,
                    url=url,
                    author=hit.get("author"),
                    timestamp=created,
                    score=hit.get("points"),
                    metadata={
                        "type": tags,
                        "object_id": object_id,
                        "num_comments": hit.get("num_comments"),
                    },
                )
            )
        return results

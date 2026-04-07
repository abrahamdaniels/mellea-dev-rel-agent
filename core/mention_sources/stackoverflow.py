from __future__ import annotations

from datetime import datetime, timezone

import httpx

from core.mention_sources import MentionSource
from core.models import Mention

_API_URL = "https://api.stackexchange.com/2.3/search/excerpts"


class StackOverflowSource(MentionSource):
    @property
    def source_name(self) -> str:
        return "stackoverflow"

    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        since_ts = int(
            since.replace(tzinfo=timezone.utc).timestamp()
            if since.tzinfo is None
            else since.timestamp()
        )
        params = {
            "order": "desc",
            "sort": "activity",
            "q": keyword,
            "site": "stackoverflow",
            "fromdate": str(since_ts),
            "pagesize": "25",
        }
        try:
            resp = httpx.get(_API_URL, params=params, timeout=15)
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        items = resp.json().get("items", [])
        mentions: list[Mention] = []

        for item in items:
            created = datetime.fromtimestamp(
                item.get("creation_date", 0), tz=timezone.utc
            )
            item_type = item.get("item_type", "question")
            item_id = item.get("question_id", "")

            if item_type == "answer":
                url = f"https://stackoverflow.com/a/{item.get('answer_id', item_id)}"
            else:
                url = f"https://stackoverflow.com/q/{item_id}"

            mentions.append(
                Mention(
                    source="stackoverflow",
                    title=item.get("title", ""),
                    content=item.get("excerpt", ""),
                    url=url,
                    author=None,
                    timestamp=created,
                    score=item.get("score"),
                    metadata={
                        "item_type": item_type,
                        "question_id": item_id,
                        "tags": item.get("tags", []),
                        "has_accepted_answer": item.get("has_accepted_answer", False),
                    },
                )
            )

        mentions.sort(key=lambda m: m.timestamp, reverse=True)
        return mentions

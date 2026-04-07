from __future__ import annotations

from datetime import datetime, timezone

import httpx

from core.config import get_config
from core.mention_sources import MentionSource
from core.models import Mention

_GRAPHQL_URL = "https://api.github.com/graphql"

_SEARCH_QUERY = """
query($query: String!, $first: Int!) {
  search(query: $query, type: DISCUSSION, first: $first) {
    edges {
      node {
        ... on Discussion {
          title
          bodyText
          url
          createdAt
          author { login }
          upvoteCount
          repository { nameWithOwner }
        }
      }
    }
  }
}
"""

_ISSUE_SEARCH_QUERY = """
query($query: String!, $first: Int!) {
  search(query: $query, type: ISSUE, first: $first) {
    edges {
      node {
        ... on Issue {
          title
          bodyText
          url
          createdAt
          author { login }
          repository { nameWithOwner }
        }
        ... on PullRequest {
          title
          bodyText
          url
          createdAt
          author { login }
          repository { nameWithOwner }
        }
      }
    }
  }
}
"""


class GitHubDiscussionsSource(MentionSource):
    @property
    def source_name(self) -> str:
        return "github_discussions"

    def is_available(self) -> bool:
        config = get_config()
        return bool(config.github_token)

    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        config = get_config()
        if not config.github_token:
            return []

        headers = {
            "Authorization": f"Bearer {config.github_token}",
            "Content-Type": "application/json",
        }
        since_str = since.strftime("%Y-%m-%d")
        repo = config.github_repo
        mentions: list[Mention] = []

        # Search discussions in the main repo
        disc_query = f'repo:{repo} "{keyword}" updated:>{since_str}'
        mentions.extend(self._run_query(_SEARCH_QUERY, disc_query, headers))

        # Search issues/PRs mentioning keyword outside the main repo
        issue_query = f'"{keyword}" NOT repo:{repo} updated:>{since_str}'
        mentions.extend(self._run_query(_ISSUE_SEARCH_QUERY, issue_query, headers))

        mentions.sort(key=lambda m: m.timestamp, reverse=True)
        return mentions

    def _run_query(
        self, query: str, search_query: str, headers: dict
    ) -> list[Mention]:
        try:
            resp = httpx.post(
                _GRAPHQL_URL,
                json={"query": query, "variables": {"query": search_query, "first": 25}},
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        data = resp.json()
        edges = data.get("data", {}).get("search", {}).get("edges", [])
        results: list[Mention] = []

        for edge in edges:
            node = edge.get("node", {})
            if not node:
                continue

            created_str = node.get("createdAt", "")
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                created = datetime.now(tz=timezone.utc)

            author_obj = node.get("author") or {}
            results.append(
                Mention(
                    source="github_discussions",
                    title=node.get("title", ""),
                    content=node.get("bodyText", "")[:500],
                    url=node.get("url", ""),
                    author=author_obj.get("login"),
                    timestamp=created,
                    score=node.get("upvoteCount"),
                    metadata={
                        "repo": (node.get("repository") or {}).get("nameWithOwner", ""),
                    },
                )
            )
        return results

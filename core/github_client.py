from __future__ import annotations

import logging
import time
from typing import Any, TypeVar

import httpx
from github import Github, GithubException, RateLimitExceededException
from github.Repository import Repository

from core.config import DevRelConfig, get_config
from core.models import (
    IssueData,
    PRData,
    ReleaseData,
    RepoStats,
    RetryPolicy,
    TreeEntry,
)

logger = logging.getLogger(__name__)

_GRAPHQL_URL = "https://api.github.com/graphql"

T = TypeVar("T")


class GitHubClient:
    def __init__(self, config: DevRelConfig | None = None):
        self._config = config or get_config()
        self._gh = Github(self._config.github_token) if self._config.github_token else Github()
        self._repo: Repository | None = None
        self._retry = RetryPolicy()

    @property
    def repo(self) -> Repository:
        if self._repo is None:
            self._repo = self._gh.get_repo(self._config.github_repo)
        return self._repo

    def _with_retry(self, fn: type[T], *args: Any, **kwargs: Any) -> T:
        delay = self._retry.backoff_base_seconds
        for attempt in range(self._retry.max_retries):
            try:
                return fn(*args, **kwargs)
            except RateLimitExceededException:
                if attempt == self._retry.max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= self._retry.backoff_multiplier
            except GithubException as e:
                if e.status == 429:
                    if attempt == self._retry.max_retries - 1:
                        raise
                    time.sleep(delay)
                    delay *= self._retry.backoff_multiplier
                else:
                    raise

    def get_pr(self, pr_number: int) -> PRData:
        """Fetch PR title, body, diff stats, changed files, comments."""
        def _fetch() -> PRData:
            pr = self.repo.get_pull(pr_number)
            files = [
                {"filename": f.filename, "additions": f.additions, "deletions": f.deletions}
                for f in pr.get_files()
            ]
            comments = [c.body for c in pr.get_issue_comments()]
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "author": pr.user.login,
                "diff_stats": {
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files,
                },
                "changed_files": files,
                "comments": comments,
                "labels": [lb.name for lb in pr.labels],
                "merged": pr.merged,
                "url": pr.html_url,
            }
        return self._with_retry(_fetch)

    def get_issue(self, issue_number: int) -> IssueData:
        """Fetch issue title, body, labels, comments."""
        def _fetch() -> IssueData:
            issue = self.repo.get_issue(issue_number)
            comments = [c.body for c in issue.get_comments()]
            return {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body or "",
                "state": issue.state,
                "author": issue.user.login,
                "labels": [lb.name for lb in issue.labels],
                "comments": comments,
                "url": issue.html_url,
            }
        return self._with_retry(_fetch)

    def get_release(self, tag: str | None = None) -> ReleaseData:
        """Fetch release (latest if no tag). Returns tag, body, assets."""
        def _fetch() -> ReleaseData:
            release = self.repo.get_latest_release() if tag is None else self.repo.get_release(tag)
            return {
                "tag": release.tag_name,
                "title": release.title,
                "body": release.body or "",
                "url": release.html_url,
                "assets": [{"name": a.name, "url": a.browser_download_url} for a in release.assets],
                "published_at": release.published_at.isoformat() if release.published_at else None,
            }
        return self._with_retry(_fetch)

    def get_repo_stats(self) -> RepoStats:
        """Fetch stars, forks, open issues count, contributor count."""
        def _fetch() -> RepoStats:
            r = self.repo
            try:
                contributor_count = sum(1 for _ in r.get_contributors())
            except GithubException:
                contributor_count = None
            return {
                "stars": r.stargazers_count,
                "forks": r.forks_count,
                "open_issues": r.open_issues_count,
                "contributors": contributor_count,
            }
        return self._with_retry(_fetch)

    def create_issue(self, title: str, body: str, labels: list[str] = []) -> int:
        """Create an issue. Returns issue number."""
        def _create():
            issue = self.repo.create_issue(title=title, body=body, labels=labels)
            return issue.number
        return self._with_retry(_create)

    def get_tree(self, path: str = "", ref: str | None = None) -> list[TreeEntry]:
        """List files in a directory of the repo.

        Returns list of dicts with keys: name, path, type (file/dir), size.
        """
        def _fetch() -> list[TreeEntry]:
            contents = self.repo.get_contents(path, ref=ref or self.repo.default_branch)
            if not isinstance(contents, list):
                contents = [contents]
            return [
                {
                    "name": c.name,
                    "path": c.path,
                    "type": "dir" if c.type == "dir" else "file",
                    "size": c.size,
                }
                for c in contents
            ]
        return self._with_retry(_fetch)

    def get_file_content(self, path: str, ref: str | None = None) -> str:
        """Read a file from the repo. Returns decoded content."""
        def _fetch():
            content = self.repo.get_contents(path, ref=ref or self.repo.default_branch)
            return content.decoded_content.decode("utf-8")
        return self._with_retry(_fetch)

    def create_pr(self, branch: str, title: str, body: str) -> int:
        """Create a PR from a branch. Returns PR number."""
        def _create():
            default_branch = self.repo.default_branch
            pr = self.repo.create_pull(title=title, body=body, head=branch, base=default_branch)
            return pr.number
        return self._with_retry(_create)

    def add_to_project_board(
        self, issue_number: int, fields: dict | None = None
    ) -> str:
        """Add an issue to the configured project board with custom fields.

        Uses GitHub Projects v2 GraphQL API.
        Returns the project item ID.
        """
        project_id = self._config.github_project_id
        if not project_id:
            raise ValueError(
                "github_project_id must be set in config to use project board."
            )

        # 1. Get issue node ID
        issue = self.repo.get_issue(issue_number)
        content_id = issue.raw_data["node_id"]

        # 2. Add item to project
        headers = {
            "Authorization": f"Bearer {self._config.github_token}",
            "Content-Type": "application/json",
        }

        add_mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(
            input: {projectId: $projectId, contentId: $contentId}
          ) { item { id } }
        }
        """

        def _add_item():
            resp = httpx.post(
                _GRAPHQL_URL,
                json={
                    "query": add_mutation,
                    "variables": {
                        "projectId": project_id,
                        "contentId": content_id,
                    },
                },
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            errors = data.get("errors")
            if errors:
                raise GithubException(422, {"errors": errors})
            return data["data"]["addProjectV2ItemById"]["item"]["id"]

        item_id = self._with_retry(_add_item)

        # 3. Update custom fields if provided
        if fields:
            field_ids = self._get_project_field_ids(project_id, headers)
            for field_name, field_value in fields.items():
                field_id = field_ids.get(field_name)
                if not field_id:
                    logger.warning(
                        "Project field '%s' not found, skipping", field_name
                    )
                    continue
                self._update_project_field(
                    project_id, item_id, field_id,
                    field_value, headers,
                )

        return item_id

    def _get_project_field_ids(
        self, project_id: str, headers: dict
    ) -> dict[str, str]:
        """Look up field name -> field ID mappings for a project."""
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 50) {
                nodes { ... on ProjectV2FieldCommon { id name } }
              }
            }
          }
        }
        """
        resp = httpx.post(
            _GRAPHQL_URL,
            json={"query": query, "variables": {"projectId": project_id}},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        nodes = (
            data.get("data", {})
            .get("node", {})
            .get("fields", {})
            .get("nodes", [])
        )
        return {n["name"]: n["id"] for n in nodes if n.get("name")}

    def _update_project_field(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        value: str,
        headers: dict,
    ) -> None:
        """Update a single text field on a project item."""
        mutation = """
        mutation(
          $projectId: ID!, $itemId: ID!,
          $fieldId: ID!, $value: String!
        ) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId, itemId: $itemId,
            fieldId: $fieldId, value: {text: $value}
          }) { projectV2Item { id } }
        }
        """
        resp = httpx.post(
            _GRAPHQL_URL,
            json={
                "query": mutation,
                "variables": {
                    "projectId": project_id,
                    "itemId": item_id,
                    "fieldId": field_id,
                    "value": value,
                },
            },
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()

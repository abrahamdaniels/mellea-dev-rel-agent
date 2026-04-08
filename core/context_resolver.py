from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from core.config import get_config
from core.github_client import GitHubClient
from core.models import ContextBlock, ContextSource

# Regex patterns for GitHub URL detection
_PR_RE = re.compile(r"github\.com/([^/]+/[^/]+)/pull/(\d+)")
_ISSUE_RE = re.compile(r"github\.com/([^/]+/[^/]+)/issues/(\d+)")
_RELEASE_RE = re.compile(r"github\.com/([^/]+/[^/]+)/releases")


def _cache_key(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _read_cache(key: str) -> dict[str, Any] | None:
    config = get_config()
    cache_file = Path(config.cache_dir) / f"{key}.json"
    if not cache_file.exists():
        return None
    data = json.loads(cache_file.read_text())
    age = time.time() - data["fetched_at"]
    if age > config.cache_ttl_seconds:
        return None
    return data["data"]


def _write_cache(key: str, data: Any) -> None:
    config = get_config()
    cache_dir = Path(config.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{key}.json"
    cache_file.write_text(json.dumps({"fetched_at": time.time(), "data": data}))


def _fetch_github_pr(url: str, no_cache: bool) -> ContextSource:
    m = _PR_RE.search(url)
    pr_number = int(m.group(2))
    key = _cache_key(url)
    if not no_cache:
        cached = _read_cache(key)
        if cached:
            return ContextSource(**cached)

    client = GitHubClient()
    data = client.get_pr(pr_number)
    content_parts = [
        f"**Title:** {data['title']}",
        f"**Author:** {data['author']}",
        f"**State:** {data['state']}",
        f"**Description:**\n{data['body']}",
        f"**Diff stats:** +{data['diff_stats']['additions']} -{data['diff_stats']['deletions']} "
        f"across {data['diff_stats']['changed_files']} files",
    ]
    if data["changed_files"]:
        file_list = "\n".join(f"  - {f['filename']}" for f in data["changed_files"][:20])
        content_parts.append(f"**Changed files:**\n{file_list}")
    if data["comments"]:
        comments_text = "\n\n".join(data["comments"][:5])
        content_parts.append(f"**Comments:**\n{comments_text}")

    source = ContextSource(
        source_type="github_pr",
        origin=url,
        title=data["title"],
        content="\n\n".join(content_parts),
        metadata={"pr_number": pr_number, "url": data["url"], "labels": data["labels"]},
    )
    if not no_cache:
        _write_cache(key, source.model_dump())
    return source


def _fetch_github_issue(url: str, no_cache: bool) -> ContextSource:
    m = _ISSUE_RE.search(url)
    issue_number = int(m.group(2))
    key = _cache_key(url)
    if not no_cache:
        cached = _read_cache(key)
        if cached:
            return ContextSource(**cached)

    client = GitHubClient()
    data = client.get_issue(issue_number)
    content_parts = [
        f"**Title:** {data['title']}",
        f"**Author:** {data['author']}",
        f"**State:** {data['state']}",
        f"**Labels:** {', '.join(data['labels']) or 'none'}",
        f"**Body:**\n{data['body']}",
    ]
    if data["comments"]:
        comments_text = "\n\n".join(data["comments"][:5])
        content_parts.append(f"**Comments:**\n{comments_text}")

    source = ContextSource(
        source_type="github_issue",
        origin=url,
        title=data["title"],
        content="\n\n".join(content_parts),
        metadata={"issue_number": issue_number, "url": data["url"]},
    )
    if not no_cache:
        _write_cache(key, source.model_dump())
    return source


def _fetch_github_release(url: str, no_cache: bool) -> ContextSource:
    key = _cache_key(url)
    if not no_cache:
        cached = _read_cache(key)
        if cached:
            return ContextSource(**cached)

    client = GitHubClient()
    data = client.get_release()
    content_parts = [
        f"**Release:** {data['tag']} - {data['title']}",
        f"**Published:** {data.get('published_at', 'unknown')}",
        f"**Release notes:**\n{data['body']}",
    ]
    source = ContextSource(
        source_type="github_release",
        origin=url,
        title=f"Release {data['tag']}",
        content="\n\n".join(content_parts),
        metadata={"tag": data["tag"], "url": data["url"]},
    )
    if not no_cache:
        _write_cache(key, source.model_dump())
    return source


def _fetch_web_url(url: str, no_cache: bool) -> ContextSource:
    key = _cache_key(url)
    if not no_cache:
        cached = _read_cache(key)
        if cached:
            return ContextSource(**cached)

    response = httpx.get(url, follow_redirects=True, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    # Remove script/style tags and extract readable text
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Collapse excessive blank lines
    lines = [line for line in text.splitlines() if line.strip()]
    content = "\n".join(lines[:500])  # cap at ~500 lines

    source = ContextSource(
        source_type="web",
        origin=url,
        title=title,
        content=content,
        metadata={"url": url, "status_code": response.status_code},
    )
    if not no_cache:
        _write_cache(key, source.model_dump())
    return source


def _read_local_file(path_str: str) -> ContextSource:
    path = Path(path_str)
    content = path.read_text(encoding="utf-8", errors="replace")
    return ContextSource(
        source_type="file",
        origin=path_str,
        title=path.name,
        content=content,
        metadata={"extension": path.suffix, "size_bytes": path.stat().st_size},
    )


def _resolve_brief(brief_str: str) -> ContextSource:
    """Load a brief by name and return as a ContextSource."""
    from core.briefs import get_brief_date, load_brief

    brief_name = brief_str.split(":", 1)[1]
    data = load_brief(brief_name)
    return ContextSource(
        source_type="brief",
        origin=brief_str,
        title=f"Brief: {brief_name}",
        content=json.dumps(data, indent=2, default=str),
        metadata={"brief_name": brief_name, "brief_date": get_brief_date(brief_name)},
    )


def _resolve_single(input_str: str, no_cache: bool) -> ContextSource:
    """Detect input type and resolve to a ContextSource."""
    s = input_str.strip()

    if s.startswith("brief:"):
        return _resolve_brief(s)
    if _PR_RE.search(s):
        return _fetch_github_pr(s, no_cache)
    if _ISSUE_RE.search(s):
        return _fetch_github_issue(s, no_cache)
    if _RELEASE_RE.search(s):
        return _fetch_github_release(s, no_cache)
    if s.startswith("http://") or s.startswith("https://"):
        return _fetch_web_url(s, no_cache)
    if Path(s).exists():
        return _read_local_file(s)

    # Raw text pass-through
    return ContextSource(
        source_type="text",
        origin=s,
        title=None,
        content=s,
        metadata={},
    )


def resolve_context(inputs: list[str], no_cache: bool = False) -> ContextBlock:
    """Resolve a list of raw input strings into a unified context block."""
    sources = [_resolve_single(inp, no_cache) for inp in inputs]
    return ContextBlock(sources=sources)

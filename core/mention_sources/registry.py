from __future__ import annotations

from core.mention_sources import MentionSource
from core.mention_sources.github_discussions import GitHubDiscussionsSource
from core.mention_sources.hackernews import HackerNewsSource
from core.mention_sources.linkedin import LinkedInSource
from core.mention_sources.pypi import PyPISource
from core.mention_sources.reddit import RedditSource
from core.mention_sources.stackoverflow import StackOverflowSource
from core.mention_sources.twitter import TwitterSource

_REGISTRY: dict[str, type[MentionSource]] = {
    "reddit": RedditSource,
    "hackernews": HackerNewsSource,
    "github_discussions": GitHubDiscussionsSource,
    "pypi": PyPISource,
    "stackoverflow": StackOverflowSource,
    "twitter": TwitterSource,
    "linkedin": LinkedInSource,
}


def get_source(name: str) -> MentionSource:
    """Get a MentionSource instance by name."""
    if name not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise ValueError(f"Unknown mention source: {name!r}. Available: {available}")
    return _REGISTRY[name]()


def get_all_sources() -> list[MentionSource]:
    """Return instances of all registered sources."""
    return [cls() for cls in _REGISTRY.values()]


def get_available_sources() -> list[MentionSource]:
    """Return instances of all sources where is_available() is True."""
    return [s for s in get_all_sources() if s.is_available()]

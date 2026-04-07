"""Asset tracker workstream agents.

Includes URL-to-platform detection utilities.
"""

from __future__ import annotations

import re

# URL pattern -> (platform, default_asset_type)
_PLATFORM_RULES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"(twitter\.com|x\.com)"), "twitter", "social_post"),
    (re.compile(r"linkedin\.com"), "linkedin", "social_post"),
    (re.compile(r"huggingface\.co/blog"), "huggingface", "blog"),
    (re.compile(r"research\.ibm\.com"), "ibm_research", "ibm_article"),
    (re.compile(r"github\.com/.+/(tree|blob)/"), "github", "demo"),
    (re.compile(r"medium\.com"), "medium", "blog"),
    (re.compile(r"dev\.to"), "dev_to", "blog"),
]


def detect_platform(url: str) -> str | None:
    """Detect the publishing platform from a URL.

    Returns one of: twitter, linkedin, huggingface, ibm_research,
    github, medium, dev_to, or None if unrecognized.
    """
    for pattern, platform, _ in _PLATFORM_RULES:
        if pattern.search(url):
            return platform
    return None


def infer_asset_type(url: str) -> str | None:
    """Infer asset type from URL. Returns None if not inferrable."""
    for pattern, _, asset_type in _PLATFORM_RULES:
        if pattern.search(url):
            return asset_type
    return None

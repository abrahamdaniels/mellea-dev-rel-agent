"""Demo workstream agents.

Includes a concept parser for extracting concepts from multi-concept markdown files.
"""

from __future__ import annotations

import re
from pathlib import Path


def parse_concept_file(path_with_selector: str) -> str:
    """Parse a concept file path with optional :N selector.

    Examples:
        "drafts/concepts.md:2"  -> returns text of Concept 2
        "drafts/concepts.md"    -> returns full file content
        "Some free text"        -> returns the text as-is (not a file)
    """
    # Try splitting on the last colon to check for :N selector
    if ":" in path_with_selector:
        base, _, selector = path_with_selector.rpartition(":")
        if selector.isdigit() and Path(base).is_file():
            content = Path(base).read_text(encoding="utf-8")
            return _extract_concept(content, int(selector))

    # No selector — check if it's a plain file path
    path = Path(path_with_selector)
    if path.is_file():
        return path.read_text(encoding="utf-8")

    # Not a file — treat as raw text (inline concept)
    return path_with_selector


def _extract_concept(content: str, number: int) -> str:
    """Extract concept N from a markdown file with ``## Concept N:`` headers."""
    pattern = re.compile(r"^## Concept \d+", re.MULTILINE)
    matches = list(pattern.finditer(content))

    if not matches:
        raise ValueError("No concepts found in file (expected ## Concept N headers)")

    if number < 1 or number > len(matches):
        raise ValueError(
            f"Concept {number} not found. File contains {len(matches)} concept(s)."
        )

    start = matches[number - 1].start()
    end = matches[number].start() if number < len(matches) else len(content)
    return content[start:end].strip()

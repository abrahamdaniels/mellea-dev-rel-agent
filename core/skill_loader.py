from __future__ import annotations

import re
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

_SKILLS_DIR = Path(__file__).parent.parent / "skills"


def _skill_path(name: str, skills_dir: Path | None = None) -> Path:
    base = skills_dir or _SKILLS_DIR
    return base / f"{name}.md"


def resolve_manifest(manifest: dict, flags: dict, skills_dir: Path | None = None) -> list[Path]:
    """Resolve a skill manifest against CLI flags.
    Returns ordered list of skill file paths."""
    paths: list[Path] = []

    for name in manifest.get("always", []):
        p = _skill_path(name, skills_dir)
        if not p.exists():
            raise FileNotFoundError(f"Skill file not found: {p}")
        paths.append(p)

    for flag_name, options in manifest.get("conditional", {}).items():
        flag_value = flags.get(flag_name)
        if flag_value is None:
            continue
        if flag_value in options:
            skill_name = options[flag_value]
            p = _skill_path(skill_name, skills_dir)
            if not p.exists():
                raise FileNotFoundError(f"Skill file not found: {p}")
            paths.append(p)

    return paths


def resolve_post_processing(manifest: dict, skills_dir: Path | None = None) -> list[Path]:
    """Return post-processing skill paths."""
    paths: list[Path] = []
    for name in manifest.get("post_processing", []):
        p = _skill_path(name, skills_dir)
        if not p.exists():
            raise FileNotFoundError(f"Skill file not found: {p}")
        paths.append(p)
    return paths


def load_skill_content(paths: list[Path]) -> str:
    """Read and concatenate skill files, stripping YAML frontmatter."""
    parts: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        text = _FRONTMATTER_RE.sub("", text, count=1).strip()
        parts.append(text)
    return "\n\n---\n\n".join(parts)

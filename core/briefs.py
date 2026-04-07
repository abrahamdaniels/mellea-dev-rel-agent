from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from core.config import get_config


def save_brief(name: str, data: dict | BaseModel) -> Path:
    """Save a brief to the briefs directory as JSON.

    Args:
        name: Brief name (e.g., 'weekly-report', 'mentions').
              Saved as briefs/latest-{name}.json.
        data: The brief data. If a BaseModel, serialized via .model_dump().

    Returns:
        Path to the saved brief file.
    """
    config = get_config()
    briefs_dir = Path(config.briefs_dir)
    briefs_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(data, BaseModel):
        payload = data.model_dump()
    else:
        payload = data

    path = briefs_dir / f"latest-{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def load_brief(name: str) -> dict[str, Any]:
    """Load a brief from the briefs directory.

    Args:
        name: Brief name (without 'latest-' prefix or '.json' suffix).

    Returns:
        Parsed JSON dict.

    Raises:
        FileNotFoundError: If the brief doesn't exist.
    """
    config = get_config()
    path = Path(config.briefs_dir) / f"latest-{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Brief '{name}' not found at {path}. "
            f"Run 'devrel monitor report' first to generate briefs."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def get_brief_date(name: str) -> str:
    """Get the modification date of a brief file. Returns ISO format string."""
    config = get_config()
    path = Path(config.briefs_dir) / f"latest-{name}.json"
    if not path.exists():
        return "unknown"
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime).isoformat()

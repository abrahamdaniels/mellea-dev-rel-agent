from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.config import get_config
from core.models import DraftOutput


def save_draft(
    agent_name: str,
    content: str,
    metadata: dict = {},
    stdout_only: bool = False,
) -> DraftOutput:
    """Save a draft to the drafts directory and print summary to stdout.
    Returns DraftOutput with the file path."""
    config = get_config()
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    filename = f"{agent_name}-{timestamp}.md"

    file_path: str | None = None
    if not stdout_only:
        drafts_dir = Path(config.drafts_dir)
        drafts_dir.mkdir(parents=True, exist_ok=True)
        dest = drafts_dir / filename
        dest.write_text(content, encoding="utf-8")
        file_path = str(dest)
        preview = content[:200].replace("\n", " ")
        print(f"\n[{agent_name}] Draft saved to {file_path}")
        print(f"Preview: {preview}...")
    else:
        print(content)

    return DraftOutput(
        agent_name=agent_name,
        content=content,
        file_path=file_path,
        metadata=metadata,
    )

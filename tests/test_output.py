from __future__ import annotations

from unittest.mock import patch

from core.config import DevRelConfig
from core.models import DraftOutput


def test_save_draft_creates_file(tmp_path):
    config = DevRelConfig(github_token="", drafts_dir=str(tmp_path / "drafts"))
    with patch("core.output.get_config", return_value=config):
        from core.output import save_draft

        result = save_draft("test-agent", "Draft content here", metadata={"key": "val"})

    assert isinstance(result, DraftOutput)
    assert result.agent_name == "test-agent"
    assert result.content == "Draft content here"
    assert result.file_path is not None
    assert (tmp_path / "drafts").exists()
    # Verify file was written
    from pathlib import Path

    written = Path(result.file_path).read_text()
    assert written == "Draft content here"


def test_save_draft_stdout_only_skips_file(tmp_path, capsys):
    config = DevRelConfig(github_token="", drafts_dir=str(tmp_path / "drafts"))
    with patch("core.output.get_config", return_value=config):
        from core.output import save_draft

        result = save_draft("test-agent", "Content for stdout", stdout_only=True)

    assert result.file_path is None
    assert not (tmp_path / "drafts").exists()
    captured = capsys.readouterr()
    assert "Content for stdout" in captured.out


def test_save_draft_returns_correct_fields():
    config = DevRelConfig(github_token="", drafts_dir="/tmp/test-drafts")
    with patch("core.output.get_config", return_value=config):
        from core.output import save_draft

        result = save_draft(
            "my-agent", "body text", metadata={"format": "blog"}, stdout_only=True
        )

    assert result.agent_name == "my-agent"
    assert result.content == "body text"
    assert result.metadata == {"format": "blog"}


def test_save_draft_creates_directory(tmp_path):
    nested = tmp_path / "deep" / "nested" / "drafts"
    config = DevRelConfig(github_token="", drafts_dir=str(nested))
    with patch("core.output.get_config", return_value=config):
        from core.output import save_draft

        result = save_draft("agent", "content")

    assert nested.exists()
    assert result.file_path is not None

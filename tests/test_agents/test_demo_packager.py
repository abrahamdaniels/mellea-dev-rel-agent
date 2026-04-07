from __future__ import annotations

from unittest.mock import MagicMock, patch

from core.models import TestResult

SAMPLE_README = """# Greeting Demo

## Overview
A demo showing Mellea structured output for greetings.

## Prerequisites
- Python 3.11+
- Mellea 0.4.2

## Usage
```bash
python main.py
```
"""


def _make_mock_llm():
    mock = MagicMock()
    mock.generate_with_template.return_value = SAMPLE_README
    return mock


def test_packager_reads_code_and_generates_readme(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')\n")
    mock_llm = _make_mock_llm()

    with patch("agents.demo.packager.LLMClient", return_value=mock_llm):
        from agents.demo.packager import run
        result = run(path=str(tmp_path), concept="Greeting demo")

    assert result.success is True
    assert (tmp_path / "README.md").exists()
    readme_content = (tmp_path / "README.md").read_text()
    assert "Greeting Demo" in readme_content


def test_packager_passes_test_results(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')\n")
    mock_llm = _make_mock_llm()
    test_result = TestResult(passed=True, total_tests=3, failed_tests=0)

    with patch("agents.demo.packager.LLMClient", return_value=mock_llm):
        from agents.demo.packager import run
        run(path=str(tmp_path), test_result=test_result)

    template_vars = mock_llm.generate_with_template.call_args[0][1]
    assert "3" in template_vars["test_output"]


def test_packager_warns_without_test_results(tmp_path, capsys):
    (tmp_path / "main.py").write_text("print('hello')\n")
    mock_llm = _make_mock_llm()

    with patch("agents.demo.packager.LLMClient", return_value=mock_llm):
        from agents.demo.packager import run
        run(path=str(tmp_path))

    captured = capsys.readouterr()
    assert "Warning" in captured.err


def test_packager_loads_skills():
    from agents.demo.packager import SKILL_MANIFEST
    from core.skill_loader import resolve_manifest

    paths = resolve_manifest(SKILL_MANIFEST, flags={})
    names = [p.stem for p in paths]
    assert "packaging" in names
    assert "mellea-knowledge" in names


def test_packager_missing_path_fails():
    from agents.demo.packager import run

    with patch("agents.demo.packager.LLMClient"):
        result = run(path="/nonexistent/demo/path")

    assert result.success is False

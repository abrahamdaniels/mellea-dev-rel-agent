from __future__ import annotations

from unittest.mock import MagicMock, patch

SAMPLE_LLM_OUTPUT = """Here are the generated files:

```main.py
from mellea import generative

@generative
def generate_greeting(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(generate_greeting("World"))
```

```test_demo.py
from main import generate_greeting

def test_greeting():
    result = generate_greeting("Test")
    assert isinstance(result, str)
```

```requirements.txt
mellea==0.4.2
```
"""


def _make_mock_llm():
    mock = MagicMock()
    mock.generate_with_template.return_value = SAMPLE_LLM_OUTPUT
    return mock


def test_code_gen_returns_success(tmp_path):
    mock_llm = _make_mock_llm()
    output_dir = str(tmp_path / "demo_out")

    with patch("agents.demo.code_gen.LLMClient", return_value=mock_llm), \
         patch("agents.demo.code_gen.resolve_context"):

        from agents.demo.code_gen import run
        result = run(concept="Build a greeting demo", output_dir=output_dir)

    assert result.success is True
    assert result.output.get("path") == output_dir


def test_code_gen_writes_files(tmp_path):
    mock_llm = _make_mock_llm()
    output_dir = str(tmp_path / "demo_out")

    with patch("agents.demo.code_gen.LLMClient", return_value=mock_llm), \
         patch("agents.demo.code_gen.resolve_context"):

        from agents.demo.code_gen import run
        run(concept="Build a greeting demo", output_dir=output_dir)

    assert (tmp_path / "demo_out" / "main.py").exists()
    assert (tmp_path / "demo_out" / "test_demo.py").exists()
    assert (tmp_path / "demo_out" / "requirements.txt").exists()


def test_code_gen_passes_repair_context(tmp_path):
    mock_llm = _make_mock_llm()
    output_dir = str(tmp_path / "demo_out")

    with patch("agents.demo.code_gen.LLMClient", return_value=mock_llm), \
         patch("agents.demo.code_gen.resolve_context"):

        from agents.demo.code_gen import run
        run(
            concept="Build a demo",
            repair_context="ImportError: no module named mellea",
            attempt=1,
            output_dir=output_dir,
        )

    template_vars = mock_llm.generate_with_template.call_args[0][1]
    assert "ImportError" in template_vars["repair_context"]
    assert template_vars["attempt"] == 1


def test_code_gen_file_extraction():
    from agents.demo.code_gen import _extract_files

    files = _extract_files(SAMPLE_LLM_OUTPUT)
    assert "main.py" in files
    assert "test_demo.py" in files
    assert "requirements.txt" in files
    assert "mellea" in files["requirements.txt"]


def test_code_gen_empty_output_returns_failure(tmp_path):
    mock_llm = MagicMock()
    mock_llm.generate_with_template.return_value = "No code blocks here."
    output_dir = str(tmp_path / "demo_out")

    with patch("agents.demo.code_gen.LLMClient", return_value=mock_llm), \
         patch("agents.demo.code_gen.resolve_context"):

        from agents.demo.code_gen import run
        result = run(concept="Build a demo", output_dir=output_dir)

    assert result.success is False
    assert "extractable" in result.error_context

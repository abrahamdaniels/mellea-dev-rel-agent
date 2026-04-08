from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from core.config import DevRelConfig


def _make_config(**overrides):
    defaults = {
        "github_token": "",
        "llm_backend": "ollama",
        "llm_model": "test-model",
    }
    defaults.update(overrides)
    return DevRelConfig(**defaults)


def test_generate_calls_backend():
    config = _make_config()
    from core.llm_client import LLMClient

    client = LLMClient(config=config)
    client._backend = MagicMock()
    client._backend.generate.return_value = "hello world"

    result = client.generate("test prompt")

    assert result == "hello world"
    client._backend.generate.assert_called_once_with("test prompt")


def test_generate_with_template_renders_and_generates(tmp_path):
    # Create a minimal template
    tmpl_dir = tmp_path / "content"
    tmpl_dir.mkdir()
    (tmpl_dir / "test.j2").write_text("Hello {{ name }}! {{ greeting }}")

    config = _make_config()
    with patch("core.llm_client._TEMPLATES_DIR", tmp_path):
        from core.llm_client import LLMClient

        client = LLMClient(config=config)
        client._backend = MagicMock()
        client._backend.generate.return_value = "generated output"

        result = client.generate_with_template(
            "content/test", {"name": "World", "greeting": "Hi"}
        )

    assert result == "generated output"
    # Verify the rendered prompt was passed to generate
    call_args = client._backend.generate.call_args
    assert "Hello World! Hi" in call_args[0][0]


def test_generate_structured_fallback_parses_json():
    config = _make_config()

    class TestOutput(BaseModel):
        value: str
        count: int

    from core.llm_client import LLMClient

    client = LLMClient(config=config)
    client._backend = MagicMock()
    client._backend.generate.return_value = '```json\n{"value": "test", "count": 42}\n```'

    # Mellea is not installed in test env, so fallback path is exercised
    result = client.generate_structured("parse this", TestOutput)

    assert isinstance(result, TestOutput)
    assert result.value == "test"
    assert result.count == 42


def test_backend_selection_ollama():
    config = _make_config(llm_backend="ollama", llm_model="granite")
    from core.llm_client import LLMClient, _OllamaBackend

    client = LLMClient(config=config)
    assert isinstance(client._backend, _OllamaBackend)
    assert client._backend.model == "granite"


def test_backend_selection_openai():
    config = _make_config(llm_backend="openai", llm_model="gpt-4", openai_api_key="sk-test")
    from core.llm_client import LLMClient, _OpenAIBackend

    client = LLMClient(config=config)
    assert isinstance(client._backend, _OpenAIBackend)
    assert client._backend.model == "gpt-4"


def test_backend_selection_claude():
    config = _make_config(llm_backend="claude", llm_model="claude-3-5-sonnet-20241022", anthropic_api_key="sk-ant-test")
    from core.llm_client import LLMClient, _ClaudeBackend

    client = LLMClient(config=config)
    assert isinstance(client._backend, _ClaudeBackend)
    assert client._backend.model == "claude-3-5-sonnet-20241022"


def test_backend_selection_unknown_raises():
    config = _make_config(llm_backend="unknown_backend")
    from core.llm_client import LLMClient

    with pytest.raises(ValueError, match="Unknown LLM backend"):
        LLMClient(config=config)


def test_agent_override_model():
    config = _make_config(llm_overrides={"sentiment": "small-model"})
    from core.llm_client import LLMClient

    client = LLMClient(config=config, agent_name="sentiment")
    assert client._backend.model == "small-model"


def test_render_template_returns_string(tmp_path):
    tmpl_dir = tmp_path / "content"
    tmpl_dir.mkdir()
    (tmpl_dir / "greeting.j2").write_text("Hello {{ name }}!")

    config = _make_config()
    with patch("core.llm_client._TEMPLATES_DIR", tmp_path):
        from core.llm_client import LLMClient

        client = LLMClient(config=config)
        result = client.render_template("content/greeting", {"name": "Mellea"})

    assert result == "Hello Mellea!"

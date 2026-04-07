"""Tests for core/config.py"""
import os
from unittest.mock import patch

from core.config import DevRelConfig, _load_yaml_config


def test_default_values():
    config = DevRelConfig(github_token="test-token")
    assert config.llm_backend == "ollama"
    assert config.llm_model == "granite-3.3-8b"
    assert config.cache_ttl_seconds == 3600
    assert config.social_char_limit_twitter == 280
    assert config.social_char_limit_linkedin == 3000


def test_env_override():
    with patch.dict(os.environ, {"DEVREL_LLM_MODEL": "llama3", "DEVREL_GITHUB_TOKEN": "tok"}):
        config = DevRelConfig()
        assert config.llm_model == "llama3"


def test_yaml_loading(tmp_path):
    yaml_file = tmp_path / "config.yml"
    yaml_file.write_text("llm_backend: openai\nllm_model: gpt-4o\ngithub_token: \"\"\n")
    data = _load_yaml_config(yaml_file)
    assert data["llm_backend"] == "openai"
    assert data["llm_model"] == "gpt-4o"


def test_yaml_missing_file(tmp_path):
    data = _load_yaml_config(tmp_path / "nonexistent.yml")
    assert data == {}

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DevRelConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEVREL_", env_file=".env", extra="ignore")

    github_token: str = ""
    github_repo: str = "generative-computing/mellea"
    github_project_id: str | None = None

    llm_backend: str = "ollama"
    llm_model: str = "granite3.3:8b"
    llm_api_key: str = ""
    llm_overrides: dict[str, str] = {}
    
    # Ollama-specific configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_api_key: str = ""
    
    # OpenAI-specific configuration
    openai_api_key: str = ""
    
    # Claude/Anthropic-specific configuration
    anthropic_api_key: str = ""

    drafts_dir: str = "drafts"
    cache_dir: str = ".cache"
    cache_ttl_seconds: int = 3600

    social_char_limit_twitter: int = 280
    social_char_limit_linkedin: int = 3000

    # Monitor config
    monitor_mention_sources: list[str] = ["reddit", "hackernews", "github_discussions", "pypi"]
    monitor_keyword: str = "mellea"
    monitor_mention_lookback_days: int = 7
    briefs_dir: str = "briefs"

    # Tracker config
    tracker_project_board_id: str = ""
    tracker_label_prefix: str = "asset-tracking"
    tracker_scan_platforms: list[str] = [
        "twitter", "linkedin", "huggingface", "ibm_research",
    ]

    # Mention source credentials
    twitter_bearer_token: str = ""
    linkedin_access_token: str = ""

    # Docs config
    docs_target_dir: str = "docs"
    docs_branch_prefix: str = "devrel/docs-update"
    docs_max_files_per_pr: int = 10

    # Demo config
    demo_output_dir: str = "demos"
    demo_retry_budget: int = 2
    demo_test_timeout: int = 120

    @field_validator("github_token")
    @classmethod
    def token_required_for_github(cls, v: str) -> str:
        # Allow empty token; GitHub client will raise at call time if needed
        return v


def _load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_config() -> DevRelConfig:
    """Load config from config.yml, overridden by DEVREL_* environment variables."""
    yaml_values = _load_yaml_config(Path("config.yml"))
    return DevRelConfig(**yaml_values)

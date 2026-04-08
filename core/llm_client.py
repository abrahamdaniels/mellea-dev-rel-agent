from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from core.config import DevRelConfig, get_config

if TYPE_CHECKING:
    pass

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class LLMClient:
    def __init__(self, config: DevRelConfig | None = None, agent_name: str | None = None):
        self._config = config or get_config()
        self._agent_name = agent_name
        self._jinja = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._backend = self._resolve_backend()

    def _resolve_backend(self) -> Any:
        """Lazy-import and initialize the LLM backend."""
        overrides = self._config.llm_overrides or {}
        model = overrides.get(self._agent_name or "", self._config.llm_model)
        backend_name = self._config.llm_backend

        if backend_name == "ollama":
            return _OllamaBackend(
                model=model,
                base_url=self._config.ollama_base_url,
                api_key=self._config.ollama_api_key,
            )
        elif backend_name == "openai":
            return _OpenAIBackend(
                model=model,
                api_key=self._config.openai_api_key or self._config.llm_api_key,
            )
        elif backend_name == "claude":
            return _ClaudeBackend(
                model=model,
                api_key=self._config.anthropic_api_key or self._config.llm_api_key,
            )
        else:
            raise ValueError(f"Unknown LLM backend: {backend_name!r}")

    def generate(self, prompt: str) -> str:
        """Simple text generation. Returns raw string output."""
        return self._backend.generate(prompt)

    def render_template(self, template_name: str, variables: dict) -> str:
        """Load a Jinja2 template and render with variables. Returns the rendered string."""
        template = self._jinja.get_template(f"{template_name}.j2")
        return template.render(**variables)

    def generate_with_template(self, template_name: str, variables: dict) -> str:
        """Load a Jinja2 template, render with variables, generate."""
        prompt = self.render_template(template_name, variables)
        return self.generate(prompt)

    def generate_structured(
        self, prompt: str, output_type: type, requirements: list | None = None
    ) -> Any:
        """Structured output with Mellea @generative or instruct(format=...).
        Falls back to JSON parsing if Mellea is unavailable."""
        try:
            import mellea  # type: ignore

            with mellea.start_session(backend=self._config.llm_backend) as session:
                result = session.instruct(
                    prompt=prompt,
                    format=output_type,
                    requirements=requirements or [],
                    loop_budget=3,
                )
            return result
        except ImportError:
            # Fallback: generate raw and attempt JSON parse into the model
            raw = self.generate(prompt)
            return _parse_structured_fallback(raw, output_type)


def _parse_structured_fallback(raw: str, output_type: type) -> Any:
    """Best-effort: extract JSON from generated text and parse into output_type."""
    import json
    import re

    # Try to find a JSON block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
    else:
        # Try parsing the whole response as JSON
        data = json.loads(raw)
    return output_type(**data)


class _OllamaBackend:
    def __init__(self, model: str, base_url: str = "http://localhost:11434", api_key: str = ""):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        import httpx

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            headers=headers if headers else None,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]


class _OpenAIBackend:
    def __init__(self, model: str, api_key: str = ""):
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        import openai  # type: ignore

        # Use provided API key or fall back to environment variable
        client = openai.OpenAI(api_key=self.api_key if self.api_key else None)
        completion = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content or ""


class _ClaudeBackend:
    def __init__(self, model: str, api_key: str = ""):
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        import anthropic  # type: ignore

        # Use provided API key or fall back to environment variable
        client = anthropic.Anthropic(api_key=self.api_key if self.api_key else None)
        message = client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text or ""

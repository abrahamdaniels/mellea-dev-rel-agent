# Testing Guide

## Quick Start

```bash
# Install in development mode with dev dependencies
# -e: editable install (changes take effect immediately)
# [dev]: includes testing tools (pytest, mypy, ruff)
# Note: On macOS, use python3 -m pip instead of pip
python3 -m pip install -e ".[dev]"

# Run all unit tests
pytest tests/ -v -m "not integration"
# Or if pytest isn't in PATH:
# python3 -m pytest tests/ -v -m "not integration"

# Run linter
ruff check .

# Fix auto-fixable lint issues
ruff check . --fix
```

## Test Organization

Tests live in `tests/` and mirror the agent structure:

| Directory | Covers |
|-----------|--------|
| `tests/test_agents/` | All agent workstreams (content, monitor, demo, tracker, docs) |
| `tests/test_mention_sources/` | Mention source plugins (Reddit, HackerNews, PyPI, GitHub Discussions) |
| `tests/` (root) | Core layer: config, context resolver, skill loader, LLM client, output, briefs, pipeline, hooks, GitHub client |
| `tests/fixtures/` | Shared test data (sample PR payloads) |

## Unit Tests

Unit tests mock all external dependencies (GitHub API, LLM backends, HTTP requests). They run without any environment variables or network access.

```bash
# Run all unit tests
pytest tests/ -v -m "not integration"

# Run a specific workstream
pytest tests/test_agents/test_technical_blog.py -v
pytest tests/test_agents/test_demo_*.py -v
pytest tests/test_agents/test_docs_*.py -v
pytest tests/test_agents/test_tracker_*.py -v
pytest tests/test_agents/test_monitor_*.py -v

# Run core layer tests only
pytest tests/test_config.py tests/test_context_resolver.py tests/test_skill_loader.py tests/test_llm_client.py -v
```

## Integration Tests

Integration tests make real API calls and require environment setup. They are marked with `@pytest.mark.integration` and skipped by default.

### Prerequisites

1. **Environment variables** (in `.env` or exported):
   ```bash
   GITHUB_TOKEN=ghp_...          # GitHub PAT with repo scope
   GITHUB_REPO=owner/repo        # Target repository
   OLLAMA_HOST=http://localhost:11434  # Ollama endpoint (optional, defaults to localhost)
   ```

2. **Ollama** running locally with a model pulled:
   ```bash
   ollama pull granite-3.3-8b
   ```

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/ -v -m "integration"

# Run with environment from .env file
export $(cat .env | xargs) && pytest tests/ -v -m "integration"
```

## E2E Smoke Tests (per workstream)

These commands verify that the CLI wiring is correct. They require the full environment setup (env vars + Ollama).

### Content Workstream

```bash
devrel content social --context "Mellea now supports streaming" --tone personal --platform twitter --stdout-only
devrel content technical-blog --context "https://github.com/generative-computing/mellea/pull/1" --stdout-only
devrel content blog-outline --context "Mellea streaming validation feature" --stdout-only
devrel content personal-blog --context "I tried Mellea's structured output" --stdout-only
devrel content suggest --stdout-only
```

### Monitor Workstream

```bash
devrel monitor report --stdout-only
devrel monitor mentions --stdout-only
devrel monitor publications --stdout-only
```

### Demo Workstream

```bash
# Full pipeline (init -> ideation -> code gen -> test -> package)
devrel demo run --context "Build a sentiment analysis demo" --stdout-only

# Individual stages
devrel demo init --context "sentiment analysis" --stdout-only
devrel demo ideation --context "sentiment analysis" --stdout-only
```

### Tracker Workstream

```bash
devrel tracker log --context "https://twitter.com/dev/status/123" --dry-run
devrel tracker sync --stdout-only
```

### Docs Workstream

```bash
devrel docs update --context "Add streaming docs" --dry-run
devrel docs review --stdout-only
```

## What to Verify

When running smoke tests, check:

1. **No import errors** - The command starts without `ModuleNotFoundError`
2. **Skills load** - No "skill file not found" warnings in output
3. **Template renders** - No Jinja2 errors
4. **LLM responds** - Output contains generated content (not empty or error text)
5. **Draft saves** - Unless `--stdout-only`, a file appears in `output/drafts/`
6. **Brief saves** - Monitor agents save briefs to `output/briefs/`

## CI vs Local

The CI pipeline (`.github/workflows/ci.yml`) runs:
- `ruff check .`
- `pytest tests/ -v -m "not integration"` on Python 3.11 and 3.12

Integration and E2E tests are local-only because they require GitHub tokens and a running Ollama instance. The `on_release.yml` and `manual_dispatch.yml` workflows run real agent invocations in GitHub Actions with secrets configured.

## Adding New Tests

Follow the existing pattern:

1. **Agent tests** go in `tests/test_agents/test_<agent_name>.py`
2. **Mock all external calls** - `LLMClient`, `GitHubClient`, `resolve_context`, `save_draft`, `save_brief`
3. **Test the skill manifest** - Verify skills resolve and load content
4. **Test the CLI wiring** - Import `run()` with mocks and verify the template name and agent name
5. **Use `tmp_path`** for any file operations

Example pattern (from `test_technical_blog.py`):

```python
def test_agent_run_calls_llm_with_template(tmp_path):
    with patch("agents.content.technical_blog.LLMClient") as MockLLM, \
         patch("agents.content.technical_blog.resolve_context") as mock_ctx, \
         patch("agents.content.technical_blog.save_draft") as mock_save:

        mock_ctx.return_value = MagicMock(
            combined_text="Context text.",
            sources=[MagicMock()],
        )
        MockLLM.return_value.generate_with_template.return_value = "# Blog"
        mock_save.return_value = DraftOutput(
            agent_name="technical-blog",
            content="# Blog",
            file_path=str(tmp_path / "blog.md"),
            metadata={"context_sources": 1},
        )

        from agents.content.technical_blog import run
        output = run(["some-context"])

    assert output.agent_name == "technical-blog"
    MockLLM.return_value.generate_with_template.assert_called_once()
```

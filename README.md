# Mellea DevRel Agent System

A CLI-driven agent system that automates developer relations work for the [Mellea](https://github.com/generative-computing/mellea) Python library. It generates content drafts, monitors adoption signals, builds demos, tracks published assets, and maintains documentation — all through a single `devrel` command.

Every agent produces a **draft for human review**. Nothing is auto-published.

## Quick Start

```bash
# Install in development mode
# -e flag: editable install (changes to source code take effect immediately)
# [dev]: includes development dependencies (pytest, mypy, ruff)
# Note: On macOS, use python3 -m pip instead of pip
python3 -m pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your GitHub token and repo

# Start Ollama (default LLM backend)
ollama pull granite3.3:8b

# Try it
devrel content suggest --stdout-only
```

## Configuration

### LLM Backend Setup

The system supports both **Ollama** (default, local) and **OpenAI** backends.

#### Using Ollama (Local)
```bash
# Install and start Ollama
ollama pull granite4:latest
ollama serve

# .env configuration (defaults)
DEVREL_LLM_BACKEND=ollama
DEVREL_LLM_MODEL=granite4.latest
DEVREL_OLLAMA_BASE_URL=http://localhost:11434
```

#### Using Ollama (Remote with API Key)
```bash
# .env configuration
DEVREL_LLM_BACKEND=ollama
DEVREL_LLM_MODEL=granite4:latest
DEVREL_OLLAMA_BASE_URL=https://ollama.example.com
DEVREL_OLLAMA_API_KEY=your_api_key_here
```

#### Using OpenAI
```bash
# .env configuration
DEVREL_LLM_BACKEND=openai
DEVREL_LLM_MODEL=gpt-4
DEVREL_OPENAI_API_KEY=sk-...
```

#### Using Claude (Anthropic)
```bash
# .env configuration
DEVREL_LLM_BACKEND=claude
DEVREL_LLM_MODEL=claude-3-5-sonnet-20241022
DEVREL_ANTHROPIC_API_KEY=sk-ant-...
```

Available Claude models: `claude-3-opus-20250219`, `claude-3-5-sonnet-20241022`, `claude-3-haiku-20250122`

#### Generic API Key Configuration
Alternatively, use the generic `DEVREL_LLM_API_KEY` for any backend:
```bash
DEVREL_LLM_BACKEND=openai
DEVREL_LLM_API_KEY=sk-...
```

## Architecture

```
devrel <workstream> <command> [--flags]
   |
   CLI Layer (Typer)
   |
   Core Layer
   |-- Context Resolver    (GitHub URLs, files, briefs, raw text -> unified context)
   |-- Skill Loader        (declarative markdown instructions, loaded per-agent)
   |-- LLM Client          (Ollama/OpenAI, Jinja2 templates, structured output via Mellea)
   |-- GitHub Client        (PRs, issues, project boards, file trees)
   |
   Agent Layer (15 specialized Python modules)
   |
   Skill Layer (markdown files with rubrics, checklists, formats)
```

Each agent follows the same pattern:
1. Resolve context inputs (URLs, files, text)
2. Load skills from its manifest
3. Render a Jinja2 template with context + skills
4. Generate via LLM
5. Save draft to `output/drafts/`

## Workstreams

### Content (5 commands)

Generate developer-facing content from context (PRs, releases, free text).

```bash
# Social media posts (Twitter + LinkedIn)
devrel content social --context "https://github.com/generative-computing/mellea/pull/42" --tone personal

# HuggingFace-style technical blog
devrel content technical-blog --context "https://github.com/generative-computing/mellea/releases"

# IBM Research blog outlidevrel content technical-blog --context "https://github.com/generative-computing/mellea/releases"ne (headers + bullets, not prose)
devrel content blog-outline --context "Mellea streaming validation feature"

# Conversational personal blog post
devrel content personal-blog --context "I tried Mellea's structured output"

# Suggest content topics from monitor data
devrel content suggest
```

**Common flags:** `--context/-c` (repeatable), `--stdout-only`, `--no-cache`

**Social-specific:** `--tone/-t` (`personal` | `ibm`), `--platform/-p` (`twitter` | `linkedin` | `both`)

### Monitor (3 commands)

Track where Mellea is being discussed and generate performance reports.

```bash
# Weekly adoption report with sentiment analysis
devrel monitor report

# Check recent mentions across platforms
devrel monitor mentions --source reddit --source hackernews

# Publications performance report (cross-references assets with mentions)
devrel monitor publications
```

**Mention sources:** Reddit, Hacker News, GitHub Discussions, PyPI, Stack Overflow, Twitter/X (requires token), LinkedIn (requires token)

**Common flags:** `--source/-s` (repeatable, filter by platform), `--stdout-only`, `--no-cache`

### Demo (5 commands)

Generate, test, and package runnable demos.

```bash
# Full pipeline: ideate -> generate code -> run tests -> package with README
devrel demo run concepts.md:1 --context "Build a sentiment analysis demo"

# Individual stages
devrel demo ideate --context "streaming validation"
devrel demo generate concepts.md:2 --context "streaming"
devrel demo test demos/sentiment-demo/
devrel demo package demos/sentiment-demo/ --concept concepts.md:1
```

The pipeline includes automatic test running and retry-on-failure with repair context.

### Tracker (2 commands)

Log published assets and find coverage gaps.

```bash
# Log an asset to the GitHub project board
devrel tracker log --context "https://twitter.com/dev/status/123" --type social_post

# Dry run (preview issue body without creating)
devrel tracker log --context "https://dev.to/post" --dry-run

# Scan for untracked assets and report gaps
devrel tracker sync
```

**Log flags:** `--type/-t`, `--title`, `--link`, `--feature`, `--dry-run`

### Docs (2 commands)

Create documentation PRs and review existing docs.

```bash
# Generate doc updates and create a PR
devrel docs update --context "Add streaming docs" --scope docs/guides/

# Dry run (preview changes without creating PR)
devrel docs update --context "Update API reference" --dry-run

# Review docs quality and LLM-readability
devrel docs review --scope docs/

# Review and auto-create GitHub issues for critical findings
devrel docs review --create-issues
```

**Update flags:** `--context/-c`, `--scope/-s`, `--dry-run`, `--stdout-only`, `--no-cache`

**Review flags:** `--scope/-s`, `--create-issues`, `--stdout-only`, `--no-cache`

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example`):

```bash
DEVREL_GITHUB_TOKEN=ghp_...              # Required: GitHub PAT with repo scope
DEVREL_GITHUB_REPO=generative-computing/mellea  # Target repository
DEVREL_GITHUB_PROJECT_ID=PVT_...         # Optional: GitHub Projects V2 board ID

# Optional: credential-gated mention sources
DEVREL_TWITTER_BEARER_TOKEN=...          # Twitter/X API v2 Bearer Token
DEVREL_LINKEDIN_ACCESS_TOKEN=...         # LinkedIn OAuth access token
```

### config.yml

The `config.yml` file controls LLM settings, output directories, and agent behavior:

```yaml
# LLM backend (ollama or openai)
llm_backend: "ollama"
llm_model: "granite-3.3-8b"

# Per-agent model overrides
llm_overrides:
  sentiment: "granite-3.3-2b"  # lighter model for classification

# Monitor settings
monitor_mention_sources:
  - reddit
  - hackernews
  - github_discussions
  - pypi
  - stackoverflow
  - twitter
  - linkedin
monitor_keyword: "mellea"
monitor_mention_lookback_days: 7

# Output directories
drafts_dir: "drafts"
cache_dir: ".cache"
cache_ttl_seconds: 3600
briefs_dir: "briefs"
```

All config values can be overridden with `DEVREL_` prefixed environment variables.

## GitHub Actions

Three workflows automate agent runs:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `ci.yml` | Push/PR to main | Runs ruff + pytest (Python 3.11 + 3.12) |
| `monitor_weekly.yml` | Mondays 9am UTC + manual | Generates weekly report + content suggestions |
| `on_release.yml` | New GitHub release | Generates social posts, technical blog, docs updates, docs review |
| `manual_dispatch.yml` | Manual trigger | Run any workstream/command with custom context |

## Testing

```bash
# Unit tests (no env vars or network needed)
pytest tests/ -v -m "not integration"

# Integration tests (requires env vars + Ollama)
pytest tests/ -v -m "integration"

# Linter
ruff check .
```

See [TESTING.md](TESTING.md) for detailed instructions, E2E smoke tests per workstream, and patterns for adding new tests.

## Type Checking

This project uses **mypy** for static type checking:

```bash
# Run type checker
mypy .

# Check specific files
mypy core/github_client.py agents/

# Verbose output
mypy --verbose .
```

See [TYPE_CHECKING.md](TYPE_CHECKING.md) for type annotation guidelines, TypedDict usage for API responses, common patterns, and troubleshooting.

## Project Structure

```
mellea-devrel/
  cli/              # Typer CLI commands (17 commands, 5 workstreams)
  core/             # Shared infrastructure (context resolver, LLM client, GitHub client, skills, briefs)
  agents/           # 15 specialized agent modules
  skills/           # Declarative markdown instructions loaded per-agent
  templates/        # Jinja2 prompt templates
  tests/            # 197 unit tests
  .github/workflows # CI + automated agent runs
  config.yml        # Runtime configuration
  .env.example      # Environment variable template
```

## Dependencies

- **Python >= 3.11**
- **[Mellea](https://github.com/generative-computing/mellea) >= 0.4.0** for structured LLM output
- **[Ollama](https://ollama.ai)** (default) or OpenAI-compatible API for LLM generation
- **GitHub PAT** with repo scope for GitHub-integrated features

## License

See the Mellea project for license terms.

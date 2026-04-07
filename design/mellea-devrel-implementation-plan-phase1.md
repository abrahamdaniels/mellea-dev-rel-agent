# Mellea DevRel Agent System - Implementation Plan

**Date:** 2026-04-05
**Design Spec:** mellea-devrel-agents-design.md
**Tool:** Cursor 3 + Claude Code

---

## How to Use This Plan

Each task is a self-contained unit of work. Tasks within a milestone are ordered
by dependency. You can hand any task to Cursor/Claude Code and it should have
enough context to implement without ambiguity.

Tasks are tagged with:
- **[code]** -- write Python code
- **[config]** -- create configuration files
- **[skill]** -- write a skill markdown file
- **[test]** -- write tests
- **[infra]** -- project setup, CI, tooling

---

## Phase 1: Foundation + Content Agent

**Goal:** `devrel content social` and `devrel content technical-blog` working
end-to-end with conditional skill loading.

**Estimated scope:** ~25 files, ~2,000 lines of code + ~1,500 lines of skill/template content.

---

### Milestone 1.1: Project Scaffold

Everything needed before any agent code can be written.

#### Task 1.1.1 [infra] Initialize the repo and Python project

Create the `mellea-devrel` directory structure, `pyproject.toml`, and basic
project configuration.

**Files to create:**
- `pyproject.toml` with dependencies:
  - `typer[all]>=0.9` (CLI)
  - `PyGithub>=2.1` (GitHub API)
  - `mellea>=0.8` (LLM reliability)
  - `jinja2>=3.1` (templates)
  - `httpx>=0.25` (HTTP client)
  - `beautifulsoup4>=4.12` (HTML parsing)
  - `pyyaml>=6.0` (config)
  - `pydantic>=2.0` (models)
  - `pydantic-settings>=2.0` (config with env vars)
  - Dev dependencies: `pytest>=7.0`, `pytest-asyncio`, `ruff`
- `README.md` with project overview and setup instructions
- `.gitignore` with entries for: `drafts/`, `briefs/`, `.cache/`, `__pycache__/`, `.env`, `*.pyc`
- `.env.example` with required environment variables:
  ```
  DEVREL_GITHUB_TOKEN=ghp_...
  DEVREL_GITHUB_REPO=generative-computing/mellea
  DEVREL_GITHUB_PROJECT_ID=PVT_...
  ```
- Empty `__init__.py` files for all packages: `cli/`, `cli/commands/`, `core/`, `agents/`, `agents/content/`

**Create all directories:**
```
mellea-devrel/
  cli/
    commands/
  core/
  agents/
    content/
  skills/
    content/
    shared/
  templates/
    content/
  tests/
    test_agents/
    fixtures/
  drafts/
  .github/
    workflows/
```

**Acceptance criteria:**
- `pip install -e .` succeeds
- `python -c "import cli; import core; import agents"` succeeds
- `ruff check .` passes with no errors

---

#### Task 1.1.2 [config] Create the configuration system

Build `core/config.py` that loads YAML config with environment variable overrides.

**File:** `core/config.py`

**Behavior:**
- Loads `config.yml` from the project root
- Environment variables prefixed with `DEVREL_` override YAML values
- Uses pydantic-settings for validation
- Exposes a singleton `get_config()` function

**Config model:**
```python
class DevRelConfig(BaseSettings):
    github_token: str
    github_repo: str                    # e.g., "generative-computing/mellea"
    github_project_id: str | None = None
    llm_backend: str = "ollama"
    llm_model: str = "granite-3.3-8b"
    llm_overrides: dict[str, str] = {}  # per-agent model overrides
    drafts_dir: str = "drafts"
    cache_dir: str = ".cache"
    cache_ttl_seconds: int = 3600       # 1 hour
    social_char_limit_twitter: int = 280
    social_char_limit_linkedin: int = 3000
```

**File:** `config.yml` (default config)

**Acceptance criteria:**
- `get_config()` loads values from YAML
- Environment variables override YAML values
- Missing required values (github_token) raise a clear error

**Test file:** `tests/test_config.py`

---

#### Task 1.1.3 [code] Create shared Pydantic models

Build `core/models.py` with the data models used across agents.

**File:** `core/models.py`

**Models:**

```python
class ContextSource(BaseModel):
    source_type: str        # "github_pr", "github_issue", "github_release", "web", "file", "text", "brief"
    origin: str             # Original input string
    title: str | None = None
    content: str
    metadata: dict = {}

class ContextBlock(BaseModel):
    sources: list[ContextSource]
    combined_text: str
    metadata: dict = {}

class DraftOutput(BaseModel):
    agent_name: str
    content: str
    file_path: str | None = None
    metadata: dict = {}         # agent-specific metadata (tone, platform, etc.)

class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_base_seconds: float = 1.0
    backoff_multiplier: float = 2.0
```

**Acceptance criteria:**
- All models serialize/deserialize cleanly
- `ContextBlock.combined_text` is computed from sources when needed

---

### Milestone 1.2: Core Layer

The shared infrastructure all agents depend on.

#### Task 1.2.1 [code] Build the Context Resolver

Build `core/context_resolver.py` that takes raw input strings and produces
a `ContextBlock`.

**File:** `core/context_resolver.py`

**Public interface:**
```python
def resolve_context(inputs: list[str]) -> ContextBlock:
    """Resolve a list of raw input strings into a unified context block."""
```

**Detection logic (in order):**
1. GitHub PR URL: regex `github\.com/.+/pull/\d+` -> fetch via GitHub API
2. GitHub Issue URL: regex `github\.com/.+/issues/\d+` -> fetch via GitHub API
3. GitHub Release URL: regex `github\.com/.+/releases/` -> fetch via GitHub API
4. Web URL: starts with `http://` or `https://` -> fetch via httpx, extract text with BeautifulSoup
5. Local file: `Path(input).exists()` -> read file, detect type from extension
6. Raw text: everything else -> pass through as-is

**Caching:**
- GitHub API responses and web fetches are cached to `.cache/` with TTL from config
- Cache key: SHA256 hash of the input string
- Cache format: JSON file with `{"fetched_at": timestamp, "data": ...}`
- Skip cache when `--no-cache` flag is set (passed as parameter)

**Combined text assembly:**
- Each source gets a header: `## Source: {source_type} - {title or origin}`
- Sources are concatenated with `\n\n---\n\n` separators
- Combined text is stored in `ContextBlock.combined_text`

**Dependencies:** `core/config.py`, `core/models.py`, GitHub Client (Task 1.2.3)

**Test file:** `tests/test_context_resolver.py`
- Test each input type detection
- Test caching (fetch once, second call reads cache)
- Test mixed inputs produce correct combined text
- Use fixtures for sample GitHub API responses

**Acceptance criteria:**
- `resolve_context(["https://github.com/generative-computing/mellea/pull/676"])` returns a ContextBlock with PR title, description, and diff summary
- `resolve_context(["./README.md", "some free text"])` returns a ContextBlock with two sources
- Cached responses are used on second call within TTL

---

#### Task 1.2.2 [code] Build the Skill Loader

Build `core/skill_loader.py` that resolves skill manifests against CLI flags.

**File:** `core/skill_loader.py`

**Public interface:**
```python
def resolve_manifest(manifest: dict, flags: dict) -> list[Path]:
    """Resolve a skill manifest against CLI flags.
    Returns ordered list of skill file paths."""

def resolve_post_processing(manifest: dict) -> list[Path]:
    """Return post-processing skill paths."""

def load_skill_content(paths: list[Path]) -> str:
    """Read and concatenate skill files, stripping YAML frontmatter."""
```

**Manifest format:**
```python
{
    "always": ["content/social-post", "shared/mellea-knowledge"],
    "conditional": {
        "tone": {
            "personal": "shared/tone-personal",
            "ibm": "shared/tone-ibm",
        },
        "platform": {
            "twitter": "content/twitter-conventions",
            "linkedin": "content/linkedin-conventions",
        },
    },
    "post_processing": ["content/de-llmify"],
}
```

**Behavior:**
- Skills directory path comes from config (default: `skills/`)
- Skill names map to `{skills_dir}/{name}.md`
- YAML frontmatter (between `---` markers) is stripped before concatenation
- Skills are joined with `\n\n---\n\n` separators
- Missing skill files raise `FileNotFoundError` with a clear message naming the missing file

**Test file:** `tests/test_skill_loader.py`
- Test "always" skills always load
- Test conditional skills load only when flag matches
- Test unmatched conditional flags result in those skills being skipped
- Test post-processing returns separate list
- Test missing file raises clear error
- Test YAML frontmatter is stripped

**Acceptance criteria:**
- Given manifest with `tone: personal` conditional and flags `{"tone": "personal"}`, loads `tone-personal.md`
- Given same manifest and flags `{"tone": "ibm"}`, loads `tone-ibm.md` instead
- Given flags `{}` (no tone specified), skips the conditional skill entirely

---

#### Task 1.2.3 [code] Build the GitHub Client

Build `core/github_client.py` wrapping PyGithub for all read/write operations.

**File:** `core/github_client.py`

**Public interface:**
```python
class GitHubClient:
    def __init__(self, config: DevRelConfig): ...

    # Read operations
    def get_pr(self, pr_number: int) -> dict:
        """Fetch PR title, body, diff stats, changed files, comments."""

    def get_issue(self, issue_number: int) -> dict:
        """Fetch issue title, body, labels, comments."""

    def get_release(self, tag: str | None = None) -> dict:
        """Fetch release (latest if no tag). Returns tag, body, assets."""

    def get_repo_stats(self) -> dict:
        """Fetch stars, forks, open issues count, contributor count."""

    # Write operations
    def create_issue(self, title: str, body: str, labels: list[str] = []) -> int:
        """Create an issue. Returns issue number."""

    def add_to_project_board(self, issue_number: int, fields: dict) -> None:
        """Add an issue to the configured project board with custom fields."""

    def create_pr(self, branch: str, title: str, body: str) -> int:
        """Create a PR from a branch. Returns PR number."""
```

**Retry policy:** Uses `RetryPolicy` from models for all API calls.

**Dependencies:** `core/config.py`, `core/models.py`

**Test file:** `tests/test_github_client.py`
- Mock PyGithub responses
- Test retry on rate limit (HTTP 429)
- Test PR/issue/release data extraction

**Acceptance criteria:**
- `get_pr(676)` returns dict with keys: title, body, diff_stats, changed_files, comments
- Rate-limited responses trigger retry with backoff

---

#### Task 1.2.4 [code] Build the LLM Client

Build `core/llm_client.py` providing a unified interface for LLM calls with
optional Mellea validation.

**File:** `core/llm_client.py`

**Public interface:**
```python
class LLMClient:
    def __init__(self, config: DevRelConfig): ...

    def generate(self, prompt: str) -> str:
        """Simple text generation. Returns raw string output."""

    def generate_with_template(self, template_name: str,
                                variables: dict) -> str:
        """Load a Jinja2 template, render with variables, generate."""

    def generate_structured(self, prompt: str,
                            output_type: type[BaseModel],
                            requirements: list | None = None) -> BaseModel:
        """Structured output with Mellea @generative or instruct(format=...).
        Uses rejection sampling with budget of 3."""
```

**Template loading:**
- Templates live in `templates/` directory
- Template name maps to `templates/{name}.j2`
- Jinja2 renders the template with provided variables

**Mellea integration:**
- `generate_structured` uses `mellea.start_session()` and `instruct(format=output_type)`
- Requirements are passed through to Mellea
- Rejection sampling with `loop_budget=3` by default

**Backend selection:**
- Default backend from config
- Per-agent overrides checked via `config.llm_overrides.get(agent_name)`

**Dependencies:** `core/config.py`, Mellea, Jinja2

**Test file:** `tests/test_llm_client.py`
- Test template rendering (mock LLM call)
- Test structured output parsing
- Test backend selection from config

**Acceptance criteria:**
- `generate_with_template("content/social_post", {...})` renders template and returns generated text
- `generate_structured(prompt, SocialPost, requirements=[...])` returns a validated Pydantic model

---

#### Task 1.2.5 [code] Build the draft output utility

Build a small utility for saving drafts consistently across all agents.

**File:** `core/output.py`

**Public interface:**
```python
def save_draft(agent_name: str, content: str, metadata: dict = {},
               stdout_only: bool = False) -> DraftOutput:
    """Save a draft to the drafts directory and print summary to stdout.
    Returns DraftOutput with the file path."""
```

**Behavior:**
- Filename format: `{agent_name}-{YYYY-MM-DD-HHMMSS}.md`
- Creates `drafts/` directory if it doesn't exist
- Writes content to file
- Prints to stdout: agent name, file path, first 200 chars of content
- If `stdout_only=True`, skips file write, prints full content
- Returns `DraftOutput` model for downstream use (e.g., post-hooks in later phases)

**Dependencies:** `core/config.py`, `core/models.py`

**Acceptance criteria:**
- Draft files are created in the configured drafts directory
- `--stdout-only` flag prevents file creation

---

### Milestone 1.3: Skill Files

Write the skill files needed by the Phase 1 agents. These exist already as
drafts from the design session (see `example-skills/` in outputs). Finalize
and place them in the `skills/` directory.

#### Task 1.3.1 [skill] Write shared/mellea-knowledge.md

Finalize the Mellea knowledge base skill. See the draft in
`example-skills/shared/mellea-knowledge.md`.

**Verify:**
- All code examples use current Mellea API (check against project knowledge)
- "What Mellea is NOT" section is accurate
- Terminology section matches current docs

**File:** `skills/shared/mellea-knowledge.md`

---

#### Task 1.3.2 [skill] Write shared/tone-personal.md and shared/tone-ibm.md

Finalize both tone skills. See drafts in `example-skills/shared/`.

**File:** `skills/shared/tone-personal.md`
**File:** `skills/shared/tone-ibm.md`

---

#### Task 1.3.3 [skill] Write content/social-post.md

Finalize the social post skill. See draft in `example-skills/content/`.

**File:** `skills/content/social-post.md`

---

#### Task 1.3.4 [skill] Write content/twitter-conventions.md

New skill. Define Twitter/X-specific constraints and norms.

**File:** `skills/content/twitter-conventions.md`

**Content should cover:**
- Character limit: 280 per tweet, 25,000 per thread tweet
- Thread structure: when to use threads vs single tweets
- Code in tweets: use short snippets (3-5 lines max) or link to a gist
- Media: images get more engagement, code screenshots should use large font
- Hashtag guidance: generally skip them unless targeting a specific community
- Link behavior: URLs consume ~23 characters regardless of length
- Mention etiquette: tag relevant accounts sparingly

---

#### Task 1.3.5 [skill] Write content/linkedin-conventions.md

New skill. Define LinkedIn-specific constraints and norms.

**File:** `skills/content/linkedin-conventions.md`

**Content should cover:**
- Character limit: ~3,000 for posts, ~120 for headline
- Structure: first 2-3 lines are critical (before "see more" fold)
- Professional framing: more context and background than Twitter
- Code: use code blocks or images, longer snippets acceptable
- Engagement patterns: posts with questions or polls get more visibility
- Hashtag guidance: 3-5 relevant hashtags at the end
- Link behavior: posts with links get less reach (put link in comments or use carousel)

---

#### Task 1.3.6 [skill] Write content/de-llmify.md

The de-LLMify post-processing skill already exists at
`/mnt/skills/user/de-llmify/SKILL.md`. Copy it to `skills/content/de-llmify.md`
and adapt it:
- Remove the `/de-llmify` command prefix (agents don't use slash commands)
- Adjust the "Usage" section for the agent context (it receives a draft, not a file path)
- Keep all the word lists, structural checks, and tone rules intact

**File:** `skills/content/de-llmify.md`

---

#### Task 1.3.7 [skill] Write content/technical-blog.md

The technical blog skill already exists at
`/mnt/skills/user/write-technical-blog/SKILL.md`. Copy it to
`skills/content/technical-blog.md` and adapt:
- Remove the `/write-technical-blog` command prefix
- Adjust for agent context (receives context via Context Resolver, not CLI args)
- Add HuggingFace-specific guidance: frontmatter format, HF audience expectations,
  model-centric framing, reproducibility emphasis
- Keep all the structure, code example rules, and self-review checklist

**File:** `skills/content/technical-blog.md`

---

### Milestone 1.4: CLI and Content Agents

Build the CLI entry point and the first two content agents.

#### Task 1.4.1 [code] Build the CLI entry point

Build `cli/main.py` as the unified `devrel` command using Typer.

**File:** `cli/main.py`

**Structure:**
```python
import typer
from cli.commands import content, monitor, demo, tracker, docs

app = typer.Typer(name="devrel", help="Mellea DevRel Agent System")
app.add_typer(content.app, name="content")
# monitor, demo, tracker, docs added in later phases
```

**File:** `cli/commands/content.py`

**Commands:**
```python
app = typer.Typer(help="Content creation agents")

@app.command()
def social(
    context: list[str] = typer.Option([], "--context", "-c", help="Context inputs"),
    tone: str = typer.Option("personal", "--tone", "-t", help="Tone: personal or ibm"),
    platform: str = typer.Option("both", "--platform", "-p", help="Platform: twitter, linkedin, or both"),
    stdout_only: bool = typer.Option(False, "--stdout-only", help="Print to stdout only"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip context cache"),
):
    """Generate social media post drafts."""

@app.command()
def technical_blog(
    context: list[str] = typer.Option([], "--context", "-c"),
    stdout_only: bool = typer.Option(False, "--stdout-only"),
    no_cache: bool = typer.Option(False, "--no-cache"),
):
    """Generate a HuggingFace-style technical blog post."""
```

**Registration in pyproject.toml:**
```toml
[project.scripts]
devrel = "cli.main:app"
```

**Acceptance criteria:**
- `devrel --help` shows available workstreams
- `devrel content --help` shows social and technical-blog commands
- `devrel content social --help` shows all flags

---

#### Task 1.4.2 [code] Build the Social Post Agent

Build `agents/content/social_post.py` with full skill manifest integration.

**File:** `agents/content/social_post.py`

**Skill manifest:**
```python
SKILL_MANIFEST = {
    "always": ["content/social-post", "shared/mellea-knowledge"],
    "conditional": {
        "tone": {
            "personal": "shared/tone-personal",
            "ibm": "shared/tone-ibm",
        },
        "platform": {
            "twitter": "content/twitter-conventions",
            "linkedin": "content/linkedin-conventions",
        },
    },
    "post_processing": ["content/de-llmify"],
}
```

**Public interface:**
```python
def run(context_inputs: list[str], tone: str, platform: str,
        stdout_only: bool = False, no_cache: bool = False) -> list[DraftOutput]:
    """Generate social post drafts. Returns one DraftOutput per platform."""
```

**Behavior:**
1. Resolve context via Context Resolver
2. Resolve skills via Skill Loader with flags `{"tone": tone, "platform": platform}`
3. If platform is "both", run generation twice (once for twitter, once for linkedin) with the appropriate platform skill swapped in
4. Generate via LLM Client using `templates/content/social_post.j2`
5. Run de-llmify post-processing pass
6. Save drafts via output utility
7. Return list of DraftOutput

**File:** `templates/content/social_post.j2`

**Template structure:**
```jinja2
You are a developer relations content writer for the Mellea Python library.

{{ skills }}

## Context

{{ context }}

## Task

Generate a {{ platform }} social media post about the above context.
Tone: {{ tone }}

Follow the instructions in the skills above exactly. Produce output in the
format specified by the social-post skill.
```

**Acceptance criteria:**
- `devrel content social --context "https://github.com/generative-computing/mellea/pull/676" --tone personal --platform twitter` produces a draft under 280 characters
- `devrel content social --tone ibm --platform both --context "New streaming API"` produces two drafts (one twitter, one linkedin)
- The de-llmify pass runs and the output contains no Tier 1 LLM-tell words

---

#### Task 1.4.3 [code] Build the Technical Blog Agent

Build `agents/content/technical_blog.py` with skill manifest integration.

**File:** `agents/content/technical_blog.py`

**Skill manifest:**
```python
SKILL_MANIFEST = {
    "always": ["content/technical-blog", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": ["content/de-llmify"],
}
```

**Public interface:**
```python
def run(context_inputs: list[str], stdout_only: bool = False,
        no_cache: bool = False) -> DraftOutput:
    """Generate a technical blog post draft."""
```

**Behavior:**
1. Resolve context (typically a PR URL)
2. Load skills (always: technical-blog + mellea-knowledge)
3. Generate via LLM Client using `templates/content/technical_blog.j2`
4. Run de-llmify post-processing
5. Save draft
6. Return DraftOutput

**File:** `templates/content/technical_blog.j2`

**Acceptance criteria:**
- `devrel content technical-blog --context "https://github.com/generative-computing/mellea/pull/676"` produces a markdown file with: title, hook, motivation, walkthrough with code, trade-offs, CTA
- Code blocks in the output use fenced syntax with language specified
- Output passes the self-review checklist from the technical-blog skill

---

### Milestone 1.5: Integration Tests

End-to-end tests that verify the full pipeline works.

#### Task 1.5.1 [test] Social Post Agent integration tests

**File:** `tests/test_agents/test_social_post.py`

**Test cases:**
- Personal tone + Twitter platform: loads correct skills, produces draft under 280 chars
- IBM tone + LinkedIn platform: loads correct skills, uses "we" not "I"
- Both platforms: produces two separate drafts
- Context from a mock GitHub PR: PR content appears in the draft
- Context from raw text: text is used directly
- Mixed context (PR URL + free text): both appear in context block
- De-llmify pass: output contains no Tier 1 words from the kill list

**Approach:** Mock the LLM Client to return controlled responses. Test the
full pipeline from CLI flags through skill loading, template rendering,
and output saving.

---

#### Task 1.5.2 [test] Technical Blog Agent integration tests

**File:** `tests/test_agents/test_technical_blog.py`

**Test cases:**
- PR context: blog references the PR's feature
- Output structure: contains expected markdown sections (title, hook, motivation, walkthrough, trade-offs, CTA)
- Code blocks: all fenced with language tag
- De-llmify pass: no Tier 1 words

---

#### Task 1.5.3 [test] Context Resolver integration tests

**File:** `tests/test_context_resolver.py` (expand from Task 1.2.1)

**Additional integration tests:**
- Real GitHub API call to fetch a known PR (can be skipped in CI with `@pytest.mark.integration`)
- Cache hit/miss behavior with TTL
- Mixed input types in a single call

---

## Phase 1 Summary

**Total files:** ~25 Python files + 7 skill files + 2 template files + config files
**Total estimated lines:** ~3,500 (code + skills + templates + tests)

**Build order within Phase 1:**
```
1.1.1 Project scaffold
  |
  +-> 1.1.2 Config
  |     |
  |     +-> 1.1.3 Models
  |           |
  |           +-> 1.2.1 Context Resolver
  |           +-> 1.2.2 Skill Loader
  |           +-> 1.2.3 GitHub Client
  |           +-> 1.2.4 LLM Client
  |           +-> 1.2.5 Draft output utility
  |
  +-> 1.3.1-1.3.7 Skill files (can be written in parallel with core)
  |
  +--- All core + skills complete ---+
                                     |
                               1.4.1 CLI entry point
                                     |
                               1.4.2 Social Post Agent
                               1.4.3 Technical Blog Agent
                                     |
                               1.5.1-1.5.3 Integration tests
```

**Phase 1 exit criteria:**
- `devrel content social --context "..." --tone personal --platform twitter` produces a valid draft
- `devrel content social --tone ibm --platform both --context "..."` produces two drafts
- `devrel content technical-blog --context "..."` produces a markdown blog post
- All unit tests pass
- All integration tests pass (with mocked LLM)
- Skill files are complete and load correctly

---

## Phase 2-5: Outline

Detailed implementation plans for Phases 2-5 will be created at the start of
each phase, following the same format as Phase 1. Here is a brief outline of
what each phase covers:

### Phase 2: Monitor Agent + Intelligence Feed
- Milestone 2.1: MentionSource interface and free platform implementations (Reddit, HN, GitHub, PyPI)
- Milestone 2.2: Monitor report agent with skill files
- Milestone 2.3: Briefs system (JSON output + Context Resolver `brief:` prefix)
- Milestone 2.4: Content Suggest agent
- Milestone 2.5: Weekly GitHub Action + integration tests

### Phase 3: Demo Pipeline
- Milestone 3.1: Pipeline core component (`core/pipeline.py`) with retry logic
- Milestone 3.2: Ideation agent (standalone)
- Milestone 3.3: Code Gen agent with repair context support
- Milestone 3.4: Test Runner (pytest harness)
- Milestone 3.5: Packager agent
- Milestone 3.6: Pipeline wiring (`devrel demo run`) + integration tests

### Phase 4: Asset Tracker
- Milestone 4.1: Post-hook system (`core/hooks.py`)
- Milestone 4.2: Log Asset agent with GitHub Project board integration
- Milestone 4.3: Sync agent
- Milestone 4.4: Demo packager post-hook wiring + integration tests

### Phase 5: Docs Agents
- Milestone 5.1: Writer agent (PR-based doc updates)
- Milestone 5.2: Reviewer agent (LLM-readability evaluation)
- Milestone 5.3: Release-triggered GitHub Action
- Milestone 5.4: Integration tests

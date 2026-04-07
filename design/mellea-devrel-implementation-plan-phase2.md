# Mellea DevRel Agent System - Phase 2 Implementation Plan

**Date:** 2026-04-06
**Design Spec:** mellea-devrel-agents-design.md (updated 2026-04-06)
**Prerequisite:** Phase 1 complete (Foundation + Content Agent)
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

## Phase 2: Monitor Agent + Intelligence Feed

**Goal:** `devrel monitor report`, `devrel monitor mentions`, and
`devrel content suggest` working end-to-end. Monitor writes structured briefs
that content agents can consume via `--context brief:<name>`.

**Estimated scope:** ~20 new files, ~2,500 lines of code + ~800 lines of
skill/template content.

---

### Milestone 2.0: Phase 1 Tech Debt

Address gaps from Phase 1 before building new features.

#### Task 2.0.1 [test] Add missing core layer tests

Add dedicated test files for core modules that lack coverage.

**File:** `tests/test_github_client.py`

**Test cases:**
- `get_pr` returns expected dict keys (mock PyGithub)
- `get_issue` returns expected dict keys (mock PyGithub)
- `get_release` returns latest when no tag specified (mock PyGithub)
- `get_repo_stats` returns stars, forks, open_issues, contributors (mock PyGithub)
- `create_issue` returns issue number (mock PyGithub)
- Rate-limited response (HTTP 429) triggers retry with backoff
- Retry exhaustion raises the original exception

**File:** `tests/test_llm_client.py`

**Test cases:**
- `generate` calls the backend and returns text (mock httpx for Ollama)
- `generate_with_template` renders Jinja2 template before generation (mock backend)
- `generate_structured` with Mellea available returns parsed model (mock Mellea)
- `generate_structured` fallback extracts JSON from code fences (mock backend)
- Backend selection respects config (ollama vs openai)
- Per-agent model override is applied when configured

**File:** `tests/test_output.py`

**Test cases:**
- `save_draft` creates file in drafts directory with correct filename format
- `save_draft` with `stdout_only=True` does not create file (use capsys)
- Returned `DraftOutput` has correct agent_name, content, file_path
- Drafts directory is created if it doesn't exist

**Acceptance criteria:**
- All three test files pass
- `pytest tests/` runs clean with no failures

---

#### Task 2.0.2 [infra] Add CI workflow

Create a basic GitHub Actions CI workflow.

**File:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest tests/ -v --ignore=tests/test_agents -m "not integration"
      - run: pytest tests/test_agents/ -v -m "not integration"
```

**Acceptance criteria:**
- Workflow runs on push to main and on PRs
- Linting and tests pass in CI
- Integration tests (marked `@pytest.mark.integration`) are excluded

---

#### Task 2.0.3 [infra] Fix wheel packaging for skills and templates

Ensure `skills/` and `templates/` directories are included when the package
is installed via pip.

**File:** `pyproject.toml` (modify)

Add `skills` and `templates` to the hatch wheel packages, or use
`[tool.hatch.build.targets.wheel.force-include]` to map them:

```toml
[tool.hatch.build.targets.wheel.force-include]
"skills" = "skills"
"templates" = "templates"
```

Update `core/skill_loader.py` and `core/llm_client.py` to resolve paths
using `importlib.resources` or a project-root finder that works both in
development and installed mode.

**Acceptance criteria:**
- `pip install -e .` still works
- `pip install .` into a clean venv, then `devrel content social --help` works
- Skill and template files are accessible from the installed package

---

### Milestone 2.1: MentionSource Interface + Platform Implementations

Build the pluggable mention-fetching system.

#### Task 2.1.1 [code] Define the MentionSource interface and Mention model

**File:** `core/models.py` (modify -- add new models)

**New models:**

```python
class Mention(BaseModel):
    """A single mention of the project on an external platform."""
    source: str                  # "reddit", "hackernews", "github_discussions", "pypi", "stackoverflow"
    title: str | None = None     # Post/thread title
    content: str                 # The text containing the mention
    url: str                     # Link to the mention
    author: str | None = None
    timestamp: datetime
    score: int | None = None     # Upvotes, stars, etc. (platform-specific)
    sentiment: str | None = None # Filled in by sentiment classification later
    metadata: dict = {}          # Platform-specific extras

class MentionBatch(BaseModel):
    """Collection of mentions from a single fetch."""
    source: str
    keyword: str
    fetched_at: datetime
    mentions: list[Mention]

class MonitorReport(BaseModel):
    """Structured output of a full monitor report run."""
    generated_at: datetime
    github_stats: dict
    pypi_stats: dict
    mentions: list[Mention]
    publication_activity: list[dict]
    highlights: list[str]
    recommendations: list[str]

class ContentSuggestion(BaseModel):
    """A single content opportunity identified by the suggest agent."""
    topic: str
    why_now: str
    recommended_format: str       # "social_post", "technical_blog", "blog_outline", "demo"
    recommended_tone: str         # "personal", "ibm"
    context_reference: str        # PR URL, brief reference, or mention link
    priority: int                 # 1 = highest
```

**Acceptance criteria:**
- All models serialize/deserialize cleanly
- `Mention.timestamp` accepts ISO format strings and datetime objects

---

#### Task 2.1.2 [code] Define the MentionSource abstract base

**File:** `core/mention_sources/__init__.py`

```python
from abc import ABC, abstractmethod
from datetime import datetime
from core.models import Mention

class MentionSource(ABC):
    """Abstract interface for fetching mentions from a platform."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Platform identifier (e.g., 'reddit', 'hackernews')."""

    @abstractmethod
    def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]:
        """Fetch mentions of `keyword` since the given datetime.
        Returns a list of Mention objects, newest first."""

    def is_available(self) -> bool:
        """Check if this source is configured and reachable.
        Returns True by default; override to add checks."""
        return True
```

**Create directory:** `core/mention_sources/`

**Acceptance criteria:**
- `MentionSource` is importable from `core.mention_sources`
- Cannot instantiate directly (abstract)

---

#### Task 2.1.3 [code] Build Reddit MentionSource

**File:** `core/mention_sources/reddit.py`

**Behavior:**
- Uses Reddit's public JSON API (no OAuth needed for read-only search)
- Endpoint: `https://www.reddit.com/search.json?q={keyword}&sort=new&t=week&limit=25`
- Searches across all subreddits, but includes subreddit-specific searches for
  `r/MachineLearning`, `r/LocalLLaMA`, `r/Python` as separate queries
- Sets a descriptive `User-Agent` header (required by Reddit API)
- Parses response into `Mention` objects
- Deduplicates by URL
- Respects Reddit's rate limit (1 request per 2 seconds)

**Dependencies:** httpx

**Test file:** `tests/test_mention_sources/test_reddit.py`
- Mock httpx responses with sample Reddit JSON
- Test mention parsing (title, content, URL, author, timestamp, score)
- Test deduplication
- Test empty response handling

**Acceptance criteria:**
- `RedditSource().fetch_mentions("mellea", since=week_ago)` returns list of `Mention`
- Each mention has source="reddit", valid URL, parsed timestamp

---

#### Task 2.1.4 [code] Build Hacker News MentionSource

**File:** `core/mention_sources/hackernews.py`

**Behavior:**
- Uses HN Algolia API: `https://hn.algolia.com/api/v1/search_by_date?query={keyword}&tags=story&numericFilters=created_at_i>{since_timestamp}`
- Also fetches comments: `tags=comment` in a separate query
- Parses response into `Mention` objects
- For stories: title is the story title, content is title + optional text
- For comments: title is parent story title (from `story_title`), content is comment text

**Dependencies:** httpx

**Test file:** `tests/test_mention_sources/test_hackernews.py`
- Mock httpx responses with sample HN Algolia JSON
- Test story vs comment parsing
- Test timestamp filtering
- Test empty response handling

**Acceptance criteria:**
- `HackerNewsSource().fetch_mentions("mellea", since=week_ago)` returns list of `Mention`
- Stories and comments are both captured
- Each mention has source="hackernews", valid HN URL

---

#### Task 2.1.5 [code] Build GitHub Discussions MentionSource

**File:** `core/mention_sources/github_discussions.py`

**Behavior:**
- Uses GitHub GraphQL API to search discussions in the configured repo
- Query: `repo:{owner}/{repo} "{keyword}" updated:>{since_date}`
- Also searches issues/PRs for mentions of the keyword outside the main repo
  using: `"{keyword}" NOT repo:{owner}/{repo} is:issue OR is:pr`
- Requires `DEVREL_GITHUB_TOKEN` (already configured in Phase 1)
- Parses GraphQL response into `Mention` objects

**Dependencies:** core/github_client.py (uses the existing token/auth), httpx for GraphQL

**Test file:** `tests/test_mention_sources/test_github_discussions.py`
- Mock GraphQL responses
- Test discussion and issue/PR parsing
- Test authentication header inclusion

**Acceptance criteria:**
- `GitHubDiscussionsSource().fetch_mentions("mellea", since=week_ago)` returns mentions
- Each mention has source="github_discussions", valid URL

---

#### Task 2.1.6 [code] Build PyPI Stats Source

**File:** `core/mention_sources/pypi.py`

**Behavior:**
- Uses PyPI JSON API: `https://pypi.org/pypi/{package}/json` for package metadata
- Uses pypistats API: `https://pypistats.org/api/packages/{package}/recent` for download counts
- This is not a "mention" source in the traditional sense but provides quantitative
  data for the monitor report
- Returns a single `Mention`-like object with download stats in metadata

**Dependencies:** httpx

**Test file:** `tests/test_mention_sources/test_pypi.py`
- Mock httpx responses
- Test download stats parsing
- Test package not found handling

**Acceptance criteria:**
- `PyPISource().fetch_mentions("mellea", since=week_ago)` returns stats
- Metadata includes daily, weekly, monthly download counts

---

#### Task 2.1.7 [code] Build the MentionSource registry

**File:** `core/mention_sources/registry.py`

**Behavior:**
- Maintains a registry of available `MentionSource` implementations
- `get_source(name: str) -> MentionSource` returns the implementation for a given name
- `get_all_sources() -> list[MentionSource]` returns all registered sources
- `get_available_sources() -> list[MentionSource]` returns only sources where
  `is_available()` returns True
- Sources are registered at import time

```python
_REGISTRY: dict[str, type[MentionSource]] = {}

def register_source(cls: type[MentionSource]) -> type[MentionSource]:
    _REGISTRY[cls.source_name.fget(cls)] = cls  # type: ignore
    return cls

def get_source(name: str) -> MentionSource:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown mention source: {name}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]()

def get_all_sources() -> list[MentionSource]:
    return [cls() for cls in _REGISTRY.values()]

def get_available_sources() -> list[MentionSource]:
    return [s for s in get_all_sources() if s.is_available()]
```

Update each MentionSource implementation (Tasks 2.1.3-2.1.6) to use the
`@register_source` decorator.

**Test file:** `tests/test_mention_sources/test_registry.py`
- Test all sources are registered
- Test `get_source` returns correct type
- Test `get_source` raises ValueError for unknown source
- Test `get_available_sources` filters correctly

**Acceptance criteria:**
- `get_source("reddit")` returns `RedditSource`
- `get_all_sources()` returns all 4 implementations
- Unknown source name raises clear error

---

### Milestone 2.2: Monitor Agent + Skill Files

Build the monitor agents and their skill files.

#### Task 2.2.1 [config] Update config for monitor workstream

**File:** `config.yml` (modify)

Add monitor-specific configuration:

```yaml
# Existing config...

monitor:
  mention_sources:
    - reddit
    - hackernews
    - github_discussions
    - pypi
  keyword: "mellea"
  mention_lookback_days: 7
  briefs_dir: "briefs"
```

**File:** `core/config.py` (modify)

Add fields to `DevRelConfig`:

```python
    # Monitor config
    monitor_mention_sources: list[str] = ["reddit", "hackernews", "github_discussions", "pypi"]
    monitor_keyword: str = "mellea"
    monitor_mention_lookback_days: int = 7
    briefs_dir: str = "briefs"
```

**Acceptance criteria:**
- `get_config().monitor_mention_sources` returns the list from config.yml
- Environment variable `DEVREL_MONITOR_KEYWORD` overrides the YAML value

---

#### Task 2.2.2 [skill] Write monitor/weekly-report.md

**File:** `skills/monitor/weekly-report.md`

**Content should cover:**

```markdown
---
name: weekly-report
description: >-
  How to structure and write the weekly DevRel monitor report.
  Covers metrics presentation, mention analysis, and actionable recommendations.
applies_to: [monitor]
---

# Weekly DevRel Report

Instructions for generating the weekly monitor report.

## Report Structure

1. **Metrics Snapshot** -- GitHub stats (stars, forks, issues) with delta from previous week.
   PyPI download counts with weekly trend. Keep to key numbers, no filler.
2. **Mention Activity** -- Table of mentions grouped by source. Include: source, count,
   average sentiment, most notable mention (with link). Sort by relevance, not count.
3. **Publication Activity** -- Cross-reference with tracked assets from the project board
   (if available). List what was published this period and on which platforms.
4. **Highlights and Recommendations** -- 3-5 bullet points. Each must reference specific
   data from the sections above. No generic advice. Recommendations should be actionable
   ("write a blog post about X because mentions of Y are trending").

## Metrics Presentation Rules

- Always show absolute number AND delta (e.g., "Stars: 1,247 (+23)")
- Use percentage for trends that span multiple weeks
- Round percentages to whole numbers
- If a metric is unavailable, say "N/A" -- never fabricate numbers
- Group related metrics (GitHub metrics together, PyPI together)

## Mention Analysis Rules

- Classify sentiment as: positive, negative, neutral, or mixed
- "Notable" means: high engagement (>10 upvotes/comments), from an influential source,
  or contains specific feedback about Mellea
- Link to the original mention, not a screenshot or summary
- Include the relevant quote (1-2 sentences max) for notable mentions

## Recommendation Quality Gates

- Every recommendation must cite specific data from the report
- "Engagement is up" is not actionable. "Reddit mentions of streaming support grew 3x --
  write a technical blog about the streaming API" is actionable.
- Limit to 3-5 recommendations. More dilutes focus.
- Prioritize by potential impact, not ease of execution

## Common Mistakes

- Padding the report with metrics that haven't changed
- Listing every mention instead of curating the notable ones
- Recommendations that don't connect to the data
- Missing deltas (absolute numbers without context are useless)
```

---

#### Task 2.2.3 [skill] Write monitor/sentiment-scoring.md

**File:** `skills/monitor/sentiment-scoring.md`

**Content should cover:**

```markdown
---
name: sentiment-scoring
description: >-
  How to classify sentiment in mentions of Mellea across platforms.
  Used by the monitor agent for mention analysis.
applies_to: [monitor]
---

# Sentiment Scoring

Instructions for classifying the sentiment of mentions.

## Classification Labels

- **positive** -- Praise, enthusiasm, successful usage reports, recommendations to others,
  excitement about features. Examples: "mellea saved us hours", "love the new streaming API"
- **negative** -- Complaints, bug reports, frustration, unfavorable comparisons.
  Examples: "mellea crashed on our dataset", "why doesn't mellea support X?"
- **neutral** -- Factual mentions without emotional valence. Examples: "mellea released v0.8",
  "here's a list of LLM tools: ... mellea ..."
- **mixed** -- Contains both positive and negative signals. Examples: "mellea's API is great
  but the docs are lacking", "fast but unstable"

## Scoring Rules

- Score based on the author's expressed sentiment, not your opinion of the content
- Bug reports are negative even if politely worded
- Feature requests are neutral unless accompanied by frustration
- Comparisons are scored based on whether Mellea comes out favorably
- If the mention is primarily about another tool and Mellea is mentioned in passing,
  score based on how Mellea is characterized in that context
- Sarcasm should be interpreted (e.g., "great, another framework" is negative)

## Confidence

When sentiment is ambiguous, prefer "mixed" over guessing. The report consumer
can read the original mention and make their own judgment.

## Output Format

Return exactly one of: positive, negative, neutral, mixed
```

---

#### Task 2.2.4 [skill] Write monitor/mention-evaluation.md

**File:** `skills/monitor/mention-evaluation.md`

**Content should cover:**

```markdown
---
name: mention-evaluation
description: >-
  How to assess the relevance and importance of individual mentions.
  Used to filter noise and surface notable mentions in the report.
applies_to: [monitor]
---

# Mention Evaluation

Instructions for assessing mention relevance and importance.

## Relevance Criteria

A mention is relevant if it:
1. Refers to the Mellea Python library (not the word "mellea" in other contexts)
2. Contains substantive content (not just a name in a list with no commentary)
3. Is from a real user/developer (not automated/bot content)

## Importance Scoring

Rate each relevant mention on a 1-5 scale:

| Score | Criteria | Example |
|---|---|---|
| 5 | High engagement + specific feedback + influential source | HN front page post about Mellea |
| 4 | Specific feedback + moderate engagement OR influential author | Detailed Reddit review with 50+ upvotes |
| 3 | Specific feedback or usage report | "Used Mellea for X, here's what happened" |
| 2 | General mention with some context | "Mellea is one of several tools for structured output" |
| 1 | Passing mention, minimal context | Name appears in a tools list |

## What Makes a Mention "Notable"

Include in the report's notable column if:
- Score >= 4
- Contains a bug report or feature request (any score)
- From a recognized community member or organization
- Shows a new use case not previously seen

## Filtering Rules

- Exclude score 1 mentions from the report entirely (just count them)
- Include score 2+ in the mention table
- Highlight score 4+ as notable with a quote
```

---

#### Task 2.2.5 [code] Build the Monitor Report Agent

**File:** `agents/monitor/report.py`

**Skill manifest:**
```python
SKILL_MANIFEST = {
    "always": ["monitor/weekly-report", "monitor/sentiment-scoring"],
    "conditional": {},
    "post_processing": [],
}
```

**Public interface:**
```python
def run(
    sources: list[str] | None = None,
    stdout_only: bool = False,
    no_cache: bool = False,
) -> DraftOutput:
    """Generate a weekly monitor report.

    Args:
        sources: Filter to specific mention sources. None = all configured sources.
        stdout_only: Print to stdout only, skip file write.
        no_cache: Skip mention/stats cache.

    Returns:
        DraftOutput with the report markdown.
    """
```

**Behavior:**
1. Load config to get mention sources and keyword
2. Fetch GitHub repo stats via `GitHubClient.get_repo_stats()`
3. Fetch PyPI stats via `PyPISource` (always, regardless of source filter)
4. Fetch mentions from each configured (or filtered) source via the MentionSource registry
5. Classify sentiment for each mention using `LLMClient.generate_structured()` with
   `Literal["positive", "negative", "neutral", "mixed"]` output type
6. Load skills and generate the report via `LLMClient.generate_with_template()`
   using `templates/monitor/weekly_report.j2`
7. Save to briefs as structured JSON (`briefs/latest-weekly-report.json`)
   AND save human-readable markdown to drafts
8. Return DraftOutput

**Sentiment classification:**
```python
# Use Mellea's structured output for reliable classification
sentiment = llm.generate_structured(
    prompt=f"Classify the sentiment of this mention:\n\n{mention.content}",
    output_type=SentimentResult,  # has a single field: sentiment: Literal[...]
    requirements=["Must return exactly one of: positive, negative, neutral, mixed"],
)
```

**Template:** `templates/monitor/weekly_report.j2`

```jinja2
You are a developer relations analyst for the Mellea Python library.

{{ skills }}

## Data

### GitHub Stats
{{ github_stats }}

### PyPI Stats
{{ pypi_stats }}

### Mentions ({{ mention_count }} total)
{% for mention in mentions %}
- [{{ mention.source }}] {{ mention.title or mention.url }}
  Sentiment: {{ mention.sentiment }}
  Score: {{ mention.score }}
  {{ mention.content[:200] }}
{% endfor %}

## Task

Generate a weekly DevRel report following the structure and rules in the
skills above. Use only the data provided. Do not fabricate numbers or mentions.
```

**Dependencies:** core/mention_sources/registry.py, core/github_client.py,
core/llm_client.py, core/skill_loader.py, core/output.py

**Acceptance criteria:**
- `devrel monitor report` produces a markdown report with all 4 sections
- Sentiment is classified for each mention
- Report references specific data (no generic filler)
- Brief JSON is saved to `briefs/latest-weekly-report.json`

---

#### Task 2.2.6 [code] Build the Mentions Check Agent

**File:** `agents/monitor/mentions.py`

**Skill manifest:**
```python
SKILL_MANIFEST = {
    "always": ["monitor/mention-evaluation", "monitor/sentiment-scoring"],
    "conditional": {},
    "post_processing": [],
}
```

**Public interface:**
```python
def run(
    sources: list[str] | None = None,
    stdout_only: bool = True,    # Default to stdout for quick checks
    no_cache: bool = False,
) -> list[Mention]:
    """Fetch and classify recent mentions.

    Args:
        sources: Filter to specific mention sources. None = all configured sources.
        stdout_only: Print to stdout only (default True for mentions check).
        no_cache: Skip cache.

    Returns:
        List of Mention objects with sentiment filled in.
    """
```

**Behavior:**
1. Fetch mentions from specified sources (lighter-weight than full report)
2. Classify sentiment for each mention
3. Evaluate relevance/importance per mention-evaluation skill
4. Print formatted table to stdout: source, title (truncated), sentiment, score, URL
5. Optionally save to `briefs/latest-mentions.json`
6. Return list of classified mentions

**Acceptance criteria:**
- `devrel monitor mentions` prints a table of recent mentions with sentiment
- `devrel monitor mentions --source reddit` filters to Reddit only
- Mentions with score < 2 are excluded from output

---

### Milestone 2.3: Briefs System

Connect the monitor output to the context resolver so any agent can read briefs.

#### Task 2.3.1 [code] Implement brief JSON output in monitor agents

**File:** `core/briefs.py` (new)

**Public interface:**
```python
def save_brief(name: str, data: dict | BaseModel) -> Path:
    """Save a brief to the briefs directory as JSON.

    Args:
        name: Brief name (e.g., 'weekly-report', 'mentions', 'trending-topics').
              Saved as briefs/latest-{name}.json.
        data: The brief data. If a BaseModel, serialized via .model_dump().

    Returns:
        Path to the saved brief file.
    """

def load_brief(name: str) -> dict:
    """Load a brief from the briefs directory.

    Args:
        name: Brief name (without 'latest-' prefix or '.json' suffix).

    Returns:
        Parsed JSON dict.

    Raises:
        FileNotFoundError: If the brief doesn't exist.
    """

def get_brief_date(name: str) -> str:
    """Get the modification date of a brief file. Returns ISO format string."""
```

**Behavior:**
- Briefs directory path comes from `config.briefs_dir` (default: `briefs/`)
- Creates directory if it doesn't exist
- Filename format: `latest-{name}.json`
- JSON serialization uses `default=str` for datetime handling
- `load_brief` raises clear error if file not found

**Acceptance criteria:**
- `save_brief("weekly-report", data)` creates `briefs/latest-weekly-report.json`
- `load_brief("weekly-report")` returns the saved data
- Round-trip serialization preserves data integrity

---

#### Task 2.3.2 [code] Update Context Resolver to handle `brief:` prefix

**File:** `core/context_resolver.py` (modify)

**Changes:**
Add a new detection case in `_resolve_single` for the `brief:` prefix, before
the web URL check:

```python
# In _resolve_single, add before web URL detection:
if input_str.startswith("brief:"):
    brief_name = input_str.split(":", 1)[1]
    from core.briefs import load_brief, get_brief_date
    data = load_brief(brief_name)
    return ContextSource(
        source_type="brief",
        origin=input_str,
        title=f"Brief: {brief_name}",
        content=json.dumps(data, indent=2, default=str),
        metadata={"brief_name": brief_name, "brief_date": get_brief_date(brief_name)},
    )
```

**Test file:** `tests/test_context_resolver.py` (modify -- add tests)

**New test cases:**
- `test_brief_prefix_loads_brief` -- `resolve_context(["brief:weekly-report"])` returns
  a ContextSource with source_type="brief"
- `test_brief_not_found_raises_error` -- Missing brief raises clear error
- `test_brief_content_is_json_string` -- Brief content is JSON-formatted

**Acceptance criteria:**
- `resolve_context(["brief:weekly-report"])` works after a monitor report has run
- Brief content is included in the combined_text of the ContextBlock
- Missing brief name raises `FileNotFoundError` with a helpful message

---

#### Task 2.3.3 [code] Update monitor agents to save briefs

**File:** `agents/monitor/report.py` (modify)
**File:** `agents/monitor/mentions.py` (modify)

Update both agents to save their structured output as briefs using `core/briefs.py`:

- `report.py` saves `briefs/latest-weekly-report.json` containing:
  `{"github_stats": {...}, "pypi_stats": {...}, "mentions": [...], "highlights": [...], "recommendations": [...]}`
- `mentions.py` saves `briefs/latest-mentions.json` containing:
  `{"mentions": [...], "fetched_at": "...", "sources": [...]}`

**Acceptance criteria:**
- After `devrel monitor report`, `brief:weekly-report` is usable as `--context`
- After `devrel monitor mentions`, `brief:mentions` is usable as `--context`

---

### Milestone 2.4: Content Suggest Agent

Build the agent that bridges monitor data and content creation.

#### Task 2.4.1 [skill] Write content/suggest.md

**File:** `skills/content/suggest.md`

**Content should cover:**

```markdown
---
name: content-suggest
description: >-
  How to analyze monitor data and generate prioritized content
  recommendations. Bridges the monitor and content workstreams.
applies_to: [content]
---

# Content Suggest

Instructions for identifying and prioritizing content opportunities
from monitor data and recent project activity.

## Input Analysis

You will receive:
1. Latest monitor brief (mentions, sentiment, trends)
2. Recent GitHub releases and PRs (from context resolver)
3. Optional additional context from the user

## Opportunity Identification Rules

Look for these content triggers (in priority order):
1. **New release or major PR merged** -- always worth content. Check if it's already
   been written about.
2. **Trending mentions** -- mentions growing week-over-week, especially positive or
   mixed (mixed = opportunity to shape narrative).
3. **Feature requests** -- recurring asks in mentions = opportunity for "how to" or
   "roadmap" content.
4. **Competitor comparisons** -- mentions comparing Mellea to other tools = opportunity
   to highlight differentiators.
5. **Community questions** -- repeated questions = documentation or blog opportunity.

## Recommendation Format

For each opportunity, specify:
- **Topic**: Clear, specific (not "write about streaming" but "streaming API performance
  benchmarks vs. synchronous calls")
- **Why now**: What data triggered this recommendation (cite specific mention, release, or metric)
- **Recommended format**: social_post, technical_blog, blog_outline, personal_blog, or demo
- **Recommended tone**: personal or ibm (based on target audience and platform)
- **Context to use**: Specific --context value the user should pass to the content agent

## Prioritization Rules

- New releases > trending mentions > feature requests > competitor comparisons > questions
- High-sentiment mentions boost priority
- Content that fills a gap (feature exists, no content about it) ranks higher
- Limit to 5 recommendations max

## Common Mistakes

- Suggesting content about features that are still in development
- Recommending the same format for every opportunity
- Not providing specific --context values (the user should be able to copy-paste)
- Suggesting content that was already published (check publication activity in the brief)
```

---

#### Task 2.4.2 [code] Build the Content Suggest Agent

**File:** `agents/content/suggest.py`

**Skill manifest:**
```python
SKILL_MANIFEST = {
    "always": ["content/suggest", "shared/mellea-knowledge"],
    "conditional": {},
    "post_processing": [],
}
```

**Public interface:**
```python
def run(
    context_inputs: list[str] | None = None,
    stdout_only: bool = True,
    no_cache: bool = False,
) -> DraftOutput:
    """Generate content suggestions from monitor data.

    Args:
        context_inputs: Optional additional context. If None, reads latest briefs automatically.
        stdout_only: Print to stdout (default True -- suggestions are ephemeral).
        no_cache: Skip cache.

    Returns:
        DraftOutput with the suggestions markdown.
    """
```

**Behavior:**
1. Automatically load latest briefs as context:
   - `brief:weekly-report` (if exists)
   - `brief:mentions` (if exists)
2. If user provides additional `--context`, resolve those too and merge
3. Fetch recent GitHub releases (last 3) via GitHubClient for cross-reference
4. Load skills
5. Generate suggestions via `LLMClient.generate_with_template("content/suggest.j2")`
6. Output to stdout (default) or save to drafts
7. Return DraftOutput

**Template:** `templates/content/suggest.j2`

```jinja2
You are a developer relations strategist for the Mellea Python library.

{{ skills }}

## Monitor Data

{{ brief_content }}

## Recent GitHub Activity

{{ github_activity }}

{% if additional_context %}
## Additional Context

{{ additional_context }}
{% endif %}

## Task

Analyze the data above and produce a prioritized list of content opportunities.
Follow the format specified in the content-suggest skill. Limit to 5 recommendations.
Each recommendation must reference specific data from the monitor report.
```

**Acceptance criteria:**
- `devrel content suggest` reads latest briefs and produces suggestions
- Each suggestion includes topic, why_now, format, tone, and context reference
- Suggestions are actionable (user can copy --context values directly)

---

#### Task 2.4.3 [code] Register the suggest command in CLI

**File:** `cli/commands/content.py` (modify)

Add the `suggest` subcommand:

```python
@app.command()
def suggest(
    context: list[str] = typer.Option([], "--context", "-c", help="Additional context inputs"),
    stdout_only: bool = typer.Option(True, "--stdout-only/--save", help="Print to stdout (default) or save to file"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip context cache"),
):
    """Suggest content topics based on monitor data."""
    from agents.content.suggest import run
    run(
        context_inputs=context if context else None,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )
```

**File:** `cli/commands/monitor.py` (new)

Create the monitor command group:

```python
import typer

app = typer.Typer(help="Adoption monitoring agents")

@app.command()
def report(
    source: list[str] = typer.Option([], "--source", "-s", help="Filter mention sources"),
    stdout_only: bool = typer.Option(False, "--stdout-only", help="Print to stdout only"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache"),
):
    """Generate a weekly monitor report."""
    from agents.monitor.report import run
    run(
        sources=source if source else None,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )

@app.command()
def mentions(
    source: list[str] = typer.Option([], "--source", "-s", help="Filter mention sources"),
    stdout_only: bool = typer.Option(True, "--stdout-only/--save", help="Print to stdout (default)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache"),
):
    """Check recent mentions across platforms."""
    from agents.monitor.report import run as report_run
    from agents.monitor.mentions import run
    run(
        sources=source if source else None,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )
```

**File:** `cli/main.py` (modify)

Register the monitor command group:

```python
from cli.commands import content, monitor

app.add_typer(content.app, name="content")
app.add_typer(monitor.app, name="monitor")
```

**Acceptance criteria:**
- `devrel monitor --help` shows report and mentions commands
- `devrel monitor report --help` shows all flags
- `devrel monitor mentions --source reddit --help` works
- `devrel content suggest --help` shows the suggest command

---

### Milestone 2.5: Weekly GitHub Action + Integration Tests

#### Task 2.5.1 [config] Create the weekly monitor workflow

**File:** `.github/workflows/monitor_weekly.yml`

```yaml
name: Weekly Monitor

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9am UTC
  workflow_dispatch:        # Manual trigger

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - name: Run monitor report
        env:
          DEVREL_GITHUB_TOKEN: ${{ secrets.DEVREL_GITHUB_TOKEN }}
          DEVREL_GITHUB_REPO: ${{ secrets.DEVREL_GITHUB_REPO }}
          DEVREL_LLM_BACKEND: ${{ secrets.DEVREL_LLM_BACKEND }}
          DEVREL_LLM_MODEL: ${{ secrets.DEVREL_LLM_MODEL }}
        run: devrel monitor report
      - name: Run content suggestions
        env:
          DEVREL_GITHUB_TOKEN: ${{ secrets.DEVREL_GITHUB_TOKEN }}
          DEVREL_GITHUB_REPO: ${{ secrets.DEVREL_GITHUB_REPO }}
          DEVREL_LLM_BACKEND: ${{ secrets.DEVREL_LLM_BACKEND }}
          DEVREL_LLM_MODEL: ${{ secrets.DEVREL_LLM_MODEL }}
        run: devrel content suggest --save
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: monitor-report-${{ github.run_id }}
          path: |
            drafts/monitor-report-*.md
            drafts/content-suggest-*.md
            briefs/
          retention-days: 30
```

**Acceptance criteria:**
- Workflow is triggered weekly on Monday 9am UTC
- Can also be triggered manually via workflow_dispatch
- Report and suggestions are saved as artifacts

---

#### Task 2.5.2 [test] Monitor Report Agent integration tests

**File:** `tests/test_agents/test_monitor_report.py`

**Test cases:**
- Report loads correct skills (weekly-report + sentiment-scoring)
- Mocked mention sources return data that appears in report
- Sentiment classification is called for each mention
- Report contains all 4 sections (metrics, mentions, publications, highlights)
- Brief JSON is saved to correct path
- Source filter limits which sources are queried
- Empty mention results produce a report (not an error)
- PyPI stats are always included regardless of source filter

**Approach:** Mock all external calls (MentionSources, GitHubClient, LLMClient).
Verify the full pipeline from CLI flags through data collection, classification,
template rendering, and output saving.

---

#### Task 2.5.3 [test] Mentions Check Agent integration tests

**File:** `tests/test_agents/test_monitor_mentions.py`

**Test cases:**
- Mentions from multiple sources are aggregated
- Sentiment classification runs on each mention
- Source filter limits results
- Low-relevance mentions (score < 2) are excluded from output
- Brief JSON is saved when `--save` is used

---

#### Task 2.5.4 [test] Content Suggest Agent integration tests

**File:** `tests/test_agents/test_content_suggest.py`

**Test cases:**
- Agent reads latest briefs automatically
- Suggestions reference specific data from briefs
- Each suggestion has all required fields (topic, why_now, format, tone, context)
- Additional --context is merged with brief data
- Missing briefs (no monitor run yet) produces a helpful error or falls back gracefully
- Suggestions are limited to 5

---

#### Task 2.5.5 [test] Brief system integration tests

**File:** `tests/test_briefs.py`

**Test cases:**
- `save_brief` and `load_brief` round-trip
- Context Resolver handles `brief:weekly-report` prefix
- Context Resolver raises clear error for missing brief
- Brief metadata includes date
- Brief content appears in combined_text with correct header

---

## Phase 2 Summary

**Total new files:** ~20 Python files + 4 skill files + 2 template files + 2 workflow files
**Total estimated lines:** ~2,500 (code) + ~800 (skills + templates) + ~500 (tests)

**Build order within Phase 2:**

```
2.0.1 Missing tests (can run in parallel with 2.0.2 and 2.0.3)
2.0.2 CI workflow
2.0.3 Wheel packaging fix
  |
  +-> 2.1.1 Mention + MonitorReport models
  |     |
  |     +-> 2.1.2 MentionSource interface
  |           |
  |           +-> 2.1.3 Reddit source
  |           +-> 2.1.4 Hacker News source    (all sources can be
  |           +-> 2.1.5 GitHub Discussions     built in parallel)
  |           +-> 2.1.6 PyPI stats source
  |           |
  |           +-> 2.1.7 Registry (after all sources)
  |
  +-> 2.2.1 Config updates
  +-> 2.2.2-2.2.4 Skill files (parallel with code)
  |
  +--- All sources + skills + config complete ---+
                                                  |
                                            2.2.5 Monitor Report Agent
                                            2.2.6 Mentions Check Agent
                                                  |
                                            2.3.1 Briefs utility
                                            2.3.2 Context Resolver brief: support
                                            2.3.3 Update agents to save briefs
                                                  |
                                            2.4.1 Suggest skill
                                            2.4.2 Content Suggest Agent
                                            2.4.3 CLI registration
                                                  |
                                            2.5.1 Weekly GitHub Action
                                            2.5.2-2.5.5 Integration tests
```

**Phase 2 exit criteria:**
- `devrel monitor report` produces a complete weekly report with real mention data
- `devrel monitor mentions` prints a table of classified mentions
- `devrel content suggest` produces actionable content recommendations from monitor data
- `brief:weekly-report` and `brief:mentions` work as `--context` inputs to any agent
- Weekly GitHub Action runs on schedule
- All unit and integration tests pass (with mocked external APIs)
- CI workflow passes on push and PR

---

## Phase 3-5: Outline

Detailed implementation plans for Phases 3-5 will be created at the start of
each phase, following the same format. See the design spec for scope outlines:

### Phase 3: Demo Pipeline
- Pipeline core component, Ideation agent, Code Gen agent, Test Runner, Packager
- `devrel demo ideate` + `devrel demo run` automated pipeline

### Phase 4: Asset Tracker
- Log Asset agent, Sync agent, Post-hook system
- `devrel tracker log` + `devrel tracker sync` + auto-logging for demos

### Phase 5: Docs Agents
- Writer agent, Reviewer agent, release-triggered GitHub Action
- `devrel docs update` + `devrel docs review`

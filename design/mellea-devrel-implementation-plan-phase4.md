# Mellea DevRel Agent System - Phase 4 Implementation Plan

**Date:** 2026-04-07
**Design Spec:** mellea-devrel-agents-design.md (updated 2026-04-07, Phase 3 Complete)
**Prerequisite:** Phase 3 complete (Demo Pipeline)
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
- **[template]** -- write a Jinja2 template
- **[test]** -- write tests
- **[infra]** -- CI, tooling, workflows

---

## Phase 4: Asset Tracker

**Goal:** `devrel tracker log` creates a GitHub issue on the project board from
a published asset URL (user-initiated). `devrel tracker sync` scans for untracked
assets and reports gaps. Post-hooks fire automatically after demo packaging to
auto-log completed demos.

**Estimated scope:** ~14 new files, ~1,500 lines of code + ~400 lines of
skill/template content.

---

### Milestone 4.0: Phase 3 Tech Debt

#### Task 4.0.1 [code] Implement `add_to_project_board` in GitHub Client

The `add_to_project_board` method in `core/github_client.py` is currently a stub
(`raise NotImplementedError`). Implement it using the GitHub Projects v2 GraphQL
API.

**File:** `core/github_client.py` (modify)

**Changes:**

Replace the `add_to_project_board` stub with a working implementation:

```python
def add_to_project_board(self, issue_number: int, fields: dict) -> str:
    """Add an issue to the configured project board with custom fields.

    Uses GitHub Projects v2 GraphQL API.
    Returns the project item ID.
    """
```

**Implementation details:**
1. Get the issue's node ID via REST: `self.repo.get_issue(issue_number).raw_data["node_id"]`
2. Use `httpx.post` to the GraphQL endpoint (`https://api.github.com/graphql`) with:
   - Mutation `addProjectV2ItemById` to add the issue to the project
   - Mutation `updateProjectV2ItemFieldValue` for each custom field in `fields`
3. Requires `config.github_project_id` to be set (raise `ValueError` if missing)
4. Fields dict maps field names to values: `{"Type": "blog", "Feature": "streaming", ...}`
5. Wrap in `_with_retry` for rate limit handling

**GraphQL mutations needed:**

```graphql
mutation AddItem($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item { id }
  }
}

mutation UpdateField($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value
  }) {
    projectV2Item { id }
  }
}
```

**Note:** Field IDs must be looked up first via a query on the project. Cache
field ID mappings after first lookup to avoid repeated queries.

---

#### Task 4.0.2 [test] Add `add_to_project_board` tests

**File:** `tests/test_github_client.py` (modify)

**New test cases:**
- `add_to_project_board` calls GraphQL endpoint with correct mutation (mock httpx)
- Missing `github_project_id` raises `ValueError`
- Field values are passed through to update mutations
- Returns project item ID on success

**Pattern:** Mock `httpx.post` for GraphQL calls. Mock `self.repo.get_issue()`
for the node ID lookup.

---

### Milestone 4.1: Asset Models + Config

#### Task 4.1.1 [code] Add asset tracking models

**File:** `core/models.py` (modify)

Add:

```python
class AssetMetadata(BaseModel):
    """Metadata for a tracked DevRel asset."""
    asset_type: str          # blog, social_post, ibm_article, demo, talk
    title: str
    feature: str | None = None
    date: str                # ISO date string
    sentiment: str | None = None
    link: str
    platform: str | None = None  # twitter, linkedin, huggingface, github, etc.

class AssetExtractionResult(BaseModel):
    """Structured output from LLM-based asset metadata extraction."""
    asset_type: Literal[
        "blog", "social_post", "ibm_article", "demo", "talk"
    ]
    title: str
    feature: str
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
```

`AssetMetadata` is the full record that gets written to the GitHub issue.
`AssetExtractionResult` is the structured output from the LLM when auto-extracting
from a URL.

---

#### Task 4.1.2 [code] Add tracker config fields

**File:** `core/config.py` (modify)

Add to `DevRelConfig`:

```python
# Tracker config
tracker_project_board_id: str = ""
tracker_label_prefix: str = "asset-tracking"
tracker_scan_platforms: list[str] = [
    "twitter", "linkedin", "huggingface", "ibm_research"
]
```

**File:** `config.yml` (modify)

Add:

```yaml
# Tracker config
tracker_project_board_id: ""
tracker_label_prefix: "asset-tracking"
tracker_scan_platforms:
  - twitter
  - linkedin
  - huggingface
  - ibm_research
```

---

#### Task 4.1.3 [code] Platform detection utility

**File:** `agents/tracker/__init__.py`

Implement a URL-to-platform detection utility:

```python
def detect_platform(url: str) -> str | None:
    """Detect the publishing platform from a URL.

    Returns one of: twitter, linkedin, huggingface, ibm_research,
    github, medium, dev_to, or None if unrecognized.
    """
```

**Detection rules (ordered by specificity):**

| URL pattern | Platform | Default asset_type |
|---|---|---|
| `twitter.com` or `x.com` | twitter | social_post |
| `linkedin.com` | linkedin | social_post |
| `huggingface.co/blog` | huggingface | blog |
| `research.ibm.com` | ibm_research | ibm_article |
| `github.com/.../tree/...` or `github.com/.../blob/...` | github | demo |
| `medium.com` | medium | blog |
| `dev.to` | dev_to | blog |

Return `None` for unrecognized URLs. The caller can prompt the user or use
the LLM for classification in that case.

Also provide:

```python
def infer_asset_type(url: str) -> str | None:
    """Infer asset type from URL. Returns None if not inferrable."""
```

---

### Milestone 4.2: Tracker Skills + Templates

#### Task 4.2.1 [skill] Asset extraction skill

**File:** `skills/tracker/asset-extraction.md`

**Frontmatter:**
```yaml
---
name: asset-extraction
description: How to extract metadata from published DevRel assets
category: tracker
---
```

**Content guidance:**
- Extract the core topic or feature the asset covers
- Identify the asset type from context and URL
- Determine sentiment: is this positive coverage, neutral documentation, or
  addressing a complaint/issue?
- Extract the most descriptive title (not necessarily the page title)
- Feature should map to a specific Mellea capability when possible
- If the asset mentions multiple features, pick the primary one
- For social posts, the full text IS the content; for blogs, focus on the thesis

---

#### Task 4.2.2 [skill] Issue formatting skill

**File:** `skills/tracker/issue-formatting.md`

**Frontmatter:**
```yaml
---
name: issue-formatting
description: GitHub issue structure for tracked assets
category: tracker
---
```

**Content guidance:**
- Issue title format: `[Asset] {type}: {title}`
- Issue body uses the structured table format from design doc Section 6.4.1
- Labels: `asset-tracking` + `type:{asset_type}` (e.g., `type:blog`)
- If the asset is about a specific Mellea feature, also add `feature:{feature}`
- Keep descriptions concise — the issue is a record, not a review
- Include the original URL prominently so the asset can be found later

---

#### Task 4.2.3 [template] Asset issue body template

**File:** `templates/tracker/issue_body.j2`

**Structure:**
```
System: You are a DevRel asset tracker creating a structured GitHub issue to record a published asset.

{{ skills }}

Asset information:
- URL: {{ url }}
- Content: {{ context }}
{% if explicit_type %}
- Type (provided): {{ explicit_type }}
{% endif %}
{% if explicit_title %}
- Title (provided): {{ explicit_title }}
{% endif %}
{% if explicit_feature %}
- Feature (provided): {{ explicit_feature }}
{% endif %}

Task: Generate the issue body in the standard asset tracking format.
Use the structured table format. If explicit values are provided, use them.
Otherwise, extract the values from the content.
```

---

### Milestone 4.3: Tracker Agents

#### Task 4.3.1 [code] Log Asset agent

**File:** `agents/tracker/log_asset.py`

**SKILL_MANIFEST:**
```python
SKILL_MANIFEST = {
    "always": ["tracker/asset-extraction", "tracker/issue-formatting"],
    "conditional": {},
    "post_processing": [],
}
```

**`run()` signature:**
```python
def run(
    context_inputs: list[str],
    asset_type: str | None = None,
    title: str | None = None,
    link: str | None = None,
    feature: str | None = None,
    no_cache: bool = False,
    dry_run: bool = False,
) -> dict:
```

**Behavior:**
1. Resolve context via `resolve_context(context_inputs)` — typically a URL
2. Detect platform from the first URL in context (use `detect_platform()`)
3. If no explicit overrides provided, use LLM to extract metadata:
   - Call `llm.generate_structured(prompt, AssetExtractionResult)` with context
4. Merge explicit overrides on top of extracted values (explicit wins)
5. Build `AssetMetadata` from merged values
6. If not `dry_run`:
   - Create GitHub issue via `GitHubClient.create_issue()`
   - Add to project board via `GitHubClient.add_to_project_board()` (if project ID configured)
   - Print issue URL to stdout
7. If `dry_run`: print the issue body to stdout without creating
8. Return dict with issue_number (or None if dry_run), metadata

**Platform detection flow:**
```
URL provided → detect_platform(url) → infer_asset_type(url)
                 ↓                        ↓
            known platform?          known type?
                 ↓ yes                    ↓ yes
            use as platform          use as default type
                 ↓ no                     ↓ no
            LLM extracts             LLM extracts
```

**Agent name:** `"tracker-log-asset"`

---

#### Task 4.3.2 [code] Sync agent

**File:** `agents/tracker/sync.py`

**`run()` signature:**
```python
def run(
    scan_platforms: list[str] | None = None,
    stdout_only: bool = True,
) -> dict:
```

**Behavior:**
1. Load configured scan platforms from config (or use override)
2. Fetch existing tracked assets from GitHub issues:
   - Search for issues with label `asset-tracking` in the repo
   - Extract URLs from issue bodies (look for `| Location |` table row)
3. For each configured platform, check for known assets:
   - This is a best-effort scan — it checks briefs, drafts directory, and
     recent GitHub releases for assets that might not be tracked
4. Cross-reference: find assets in briefs/drafts that don't have matching
   tracked issues
5. Output a report listing untracked assets with suggested actions

**Report format:**
```markdown
# Asset Sync Report - {date}

## Tracked Assets: {n}
## Potentially Untracked: {m}

| Asset | Platform | Source | Suggested Action |
|---|---|---|---|
| {title} | {platform} | briefs/latest-weekly-report.json | Run: devrel tracker log --context "URL" |
```

**Note:** The sync agent does NOT auto-log. It reports findings for human
review. The user then runs `devrel tracker log` for each asset they want
to track.

**Agent name:** `"tracker-sync"`

---

### Milestone 4.4: Post-Hook System

#### Task 4.4.1 [code] Post-hook engine

**File:** `core/hooks.py`

```python
import logging

logger = logging.getLogger("hooks")

POST_HOOKS: dict[str, list[str]] = {
    "demo.packager": [
        "tracker.log_asset",
    ],
}

def run_post_hooks(agent_name: str, agent_output: dict) -> None:
    """Run post-hooks for the named agent. Best-effort: failures are logged."""
    for pattern, hooks in POST_HOOKS.items():
        if _matches(agent_name, pattern):
            for hook in hooks:
                try:
                    _invoke_hook(hook, agent_output)
                except Exception as e:
                    logger.warning("Post-hook %s failed: %s", hook, e)

def _matches(agent_name: str, pattern: str) -> bool:
    """Check if agent_name matches a hook pattern.
    Supports exact match and prefix match with dot notation."""
    return agent_name == pattern or agent_name.startswith(pattern + ".")

def _invoke_hook(hook: str, context: dict) -> None:
    """Resolve and invoke a hook by its dotted name."""
    if hook == "tracker.log_asset":
        from agents.tracker.log_asset import run
        # Build context_inputs from the agent output
        path = context.get("path", "")
        run(
            context_inputs=[path] if path else [],
            asset_type="demo",
            dry_run=False,
        )
    else:
        raise ValueError(f"Unknown hook: {hook}")
```

**Design decisions:**
- Hook registry is a static dict (not decorators, not config file) — same
  registry pattern used for MentionSources
- `_invoke_hook` does lazy imports to avoid circular dependencies
- Hooks receive the agent's output dict and extract what they need
- `--no-hooks` CLI flag is checked before calling `run_post_hooks`

---

#### Task 4.4.2 [code] Wire post-hook into demo packager

**File:** `agents/demo/packager.py` (modify)

After successful packaging, call post-hooks:

```python
# At end of run(), after success:
if not stdout_only:
    from core.hooks import run_post_hooks
    run_post_hooks("demo.packager", result.output)
```

Add a `no_hooks: bool = False` parameter to `run()` and the CLI command.

**File:** `cli/commands/demo.py` (modify)

Add `--no-hooks` flag to the `package` and `run` commands.

---

### Milestone 4.5: CLI Commands

#### Task 4.5.1 [code] CLI tracker commands

**File:** `cli/commands/tracker.py`

**Commands:**

```python
import typer
from typing import Annotated, Optional

app = typer.Typer(help="Asset tracking commands")

@app.command()
def log(
    context: Annotated[
        list[str],
        typer.Option(
            "--context", "-c",
            help="URL to published asset or free text.",
        ),
    ] = [],
    asset_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t",
            help="Asset type: blog, social_post, ibm_article, demo, talk"),
    ] = None,
    title: Annotated[
        Optional[str],
        typer.Option("--title", help="Override asset title."),
    ] = None,
    link: Annotated[
        Optional[str],
        typer.Option("--link", help="Override asset URL."),
    ] = None,
    feature: Annotated[
        Optional[str],
        typer.Option("--feature", help="Mellea feature this asset covers."),
    ] = None,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print issue body without creating."),
    ] = False,
) -> None:
    """Log a published asset to the GitHub project board."""

@app.command()
def sync(
    scan_platforms: Annotated[
        list[str],
        typer.Option("--platform", "-p", help="Platforms to scan."),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only/--save",
            help="Print report to stdout (default) or save."),
    ] = True,
) -> None:
    """Scan for untracked assets and report gaps."""
```

**File:** `cli/main.py` (modify)

Add:
```python
from cli.commands import tracker
app.add_typer(tracker.app, name="tracker")
```

---

### Milestone 4.6: Tests

#### Task 4.6.1 [test] Platform detection tests

**File:** `tests/test_agents/test_tracker_init.py`

**Test cases:**
- `detect_platform("https://twitter.com/user/status/123")` → `"twitter"`
- `detect_platform("https://x.com/user/status/123")` → `"twitter"`
- `detect_platform("https://linkedin.com/posts/...")` → `"linkedin"`
- `detect_platform("https://huggingface.co/blog/post")` → `"huggingface"`
- `detect_platform("https://unknown-site.com/post")` → `None`
- `infer_asset_type("https://twitter.com/...")` → `"social_post"`
- `infer_asset_type("https://huggingface.co/blog/...")` → `"blog"`

---

#### Task 4.6.2 [test] Log Asset agent tests

**File:** `tests/test_agents/test_tracker_log_asset.py`

**Test cases:**
- `run()` with URL context calls `generate_structured` for extraction (mock LLM)
- Explicit overrides bypass LLM extraction
- GitHub issue is created with correct title and labels (mock GitHubClient)
- Dry run prints body without creating issue
- Platform detection is used for asset type inference
- Skill manifest loads asset-extraction + issue-formatting

**Pattern:** Triple-patch (LLMClient, resolve_context, GitHubClient).

---

#### Task 4.6.3 [test] Sync agent tests

**File:** `tests/test_agents/test_tracker_sync.py`

**Test cases:**
- Sync fetches tracked issues with asset-tracking label (mock GitHubClient)
- Report lists untracked assets found in briefs
- Empty tracked list reports all found assets as untracked
- Platform filter limits which sources are scanned

**Pattern:** Mock GitHubClient and briefs loading.

---

#### Task 4.6.4 [test] Post-hook tests

**File:** `tests/test_hooks.py`

**Test cases:**
- `run_post_hooks("demo.packager", {...})` invokes tracker.log_asset (mock)
- Unknown agent name does not trigger any hooks
- Hook failure is caught and logged (does not raise)
- `_matches` correctly handles exact and prefix patterns
- `--no-hooks` flag prevents hook execution

---

#### Task 4.6.5 [test] `add_to_project_board` tests

**File:** `tests/test_github_client.py` (modify)

**New test cases:**
- GraphQL mutation is called with correct project ID and item ID
- Missing project ID raises ValueError
- Custom fields are updated via separate mutations

---

## Summary

| Milestone | Tasks | New Files | Modified Files |
|---|---|---|---|
| 4.0 Tech Debt | 2 | 0 | 2 |
| 4.1 Models + Config | 3 | 1 | 3 |
| 4.2 Skills + Templates | 3 | 3 | 0 |
| 4.3 Tracker Agents | 2 | 2 | 0 |
| 4.4 Post-Hook System | 2 | 1 | 2 |
| 4.5 CLI | 1 | 1 | 1 |
| 4.6 Tests | 5 | 4 | 1 |
| **Total** | **18** | **12** | **9** |

## Dependencies

```
Milestone 4.0 (tech debt)        -- do first (add_to_project_board needed by 4.3)
Milestone 4.1 (models/config)    -- no dependency on 4.0, can parallel
Milestone 4.2 (skills/templates) -- no dependency on 4.1, can parallel
   |
   +-- 4.0 + 4.1 + 4.2 must complete before 4.3
   |
Milestone 4.3 (agents)           -- depends on 4.0 (project board), 4.1 (models), 4.2 (skills)
Milestone 4.4 (hooks)            -- depends on 4.3 (tracker agent exists)
Milestone 4.5 (CLI)              -- depends on 4.3 (agents exist)
Milestone 4.6 (tests)            -- depends on 4.3 + 4.4 + 4.5
```

**Parallelizable:** 4.0, 4.1, and 4.2 can all be done in parallel.
4.3, 4.4, and 4.5 are sequential after 4.0+4.1+4.2. 4.6 follows last.

## Exit Criteria

- [ ] `devrel tracker log --context "https://twitter.com/..." --help` shows all flags
- [ ] `devrel tracker log --context "URL" --dry-run` prints issue body without creating
- [ ] `devrel tracker log --context "URL"` creates a GitHub issue with correct labels and project board entry
- [ ] `devrel tracker log --type blog --title "Post" --link "URL"` uses explicit values
- [ ] `devrel tracker sync --help` shows platform filter flags
- [ ] `devrel tracker sync` reports untracked assets from briefs/drafts
- [ ] Demo pipeline completion auto-logs via post-hook (unless `--no-hooks`)
- [ ] `add_to_project_board` creates project items via GraphQL
- [ ] All tests pass (`pytest tests/ -q`)
- [ ] `ruff check .` passes with no errors

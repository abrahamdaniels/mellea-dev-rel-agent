# Mellea DevRel Agent System - Phase 5 Implementation Plan

**Date:** 2026-04-07
**Design Spec:** mellea-devrel-agents-design.md (updated 2026-04-07, Phase 4 Complete)
**Prerequisite:** Phase 4 complete (Asset Tracker)
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

## Phase 5: Docs Agents

**Goal:** `devrel docs update` reads context (PR URL, changelog, feature spec)
and generates documentation updates as a GitHub PR. `devrel docs review` evaluates
existing documentation against LLM-readability criteria and reports findings.
A release-triggered GitHub Action auto-runs both content and docs agents on new
releases. A manual dispatch workflow allows running any workstream on demand.

**Estimated scope:** ~16 new files, ~1,200 lines of code + ~500 lines of
skill/template content.

---

### Milestone 5.0: Phase 4 Tech Debt

#### Task 5.0.1 [test] Add `create_pr` tests to GitHub Client

The `create_pr` method in `core/github_client.py` exists but has no tests.
It will be exercised by the Docs Writer agent. Add tests before relying on it.

**File:** `tests/test_github_client.py` (modify)

**New test cases:**
- `create_pr` calls `repo.create_pull` with correct branch, title, body, base
- Returns the PR number on success
- Uses default branch as base

**Pattern:** Mock `self.repo.create_pull()` and `self.repo.default_branch`.

---

#### Task 5.0.2 [code] Add `get_tree` and `get_file_content` to GitHub Client

The Docs Writer agent needs to discover which docs files exist in the target repo
and read their contents. Add two convenience methods.

**File:** `core/github_client.py` (modify)

**New methods:**

```python
def get_tree(self, path: str = "", ref: str | None = None) -> list[dict]:
    """List files in a directory of the repo.

    Returns list of dicts with keys: name, path, type (file/dir), size.
    """

def get_file_content(self, path: str, ref: str | None = None) -> str:
    """Read a file from the repo. Returns decoded content."""
```

**Implementation:**
- `get_tree`: Use `self.repo.get_contents(path, ref=ref)` which returns
  `ContentFile` objects. Map to simple dicts.
- `get_file_content`: Use `self.repo.get_contents(path, ref=ref)` on a single
  file, return `decoded_content.decode("utf-8")`.
- Both wrapped in `_with_retry`.

---

#### Task 5.0.3 [test] Tests for `get_tree` and `get_file_content`

**File:** `tests/test_github_client.py` (modify)

**New test cases:**
- `get_tree` returns list of file entries with correct keys
- `get_tree` on nested path works
- `get_file_content` returns decoded string
- `get_file_content` on missing file raises (pass through GitHub exception)

---

### Milestone 5.1: Docs Models + Config

#### Task 5.1.1 [code] Add docs models

**File:** `core/models.py` (modify)

Add:

```python
class DocFinding(BaseModel):
    """A single finding from documentation review."""
    file_path: str
    severity: Literal["critical", "warning", "info"]
    category: str              # e.g., "stale_api", "missing_example", "broken_link"
    description: str
    suggestion: str | None = None
    line_range: tuple[int, int] | None = None

class DocReviewReport(BaseModel):
    """Aggregate output from a docs review pass."""
    files_reviewed: int
    findings: list[DocFinding]
    summary: str

class DocUpdatePlan(BaseModel):
    """Structured plan for which doc files to update."""
    affected_files: list[str]
    reason: str
    change_type: Literal["update", "create", "deprecate"]
```

`DocFinding` is used by the Reviewer agent. `DocUpdatePlan` is used by the
Writer agent to identify which files need changes before generating content.

---

#### Task 5.1.2 [code] Add docs config fields

**File:** `core/config.py` (modify)

Add to `DevRelConfig`:

```python
# Docs config
docs_target_dir: str = "docs"          # Path within target repo to scan/update
docs_branch_prefix: str = "devrel/docs-update"  # Branch name prefix for PRs
docs_max_files_per_pr: int = 10        # Limit files per PR to keep reviews manageable
```

**File:** `config.yml` (modify)

Add:

```yaml
# Docs config
docs_target_dir: "docs"
docs_branch_prefix: "devrel/docs-update"
docs_max_files_per_pr: 10
```

---

### Milestone 5.2: Docs Skills + Templates

#### Task 5.2.1 [skill] Writing standards skill

**File:** `skills/docs/writing-standards.md`

**Frontmatter:**
```yaml
---
name: writing-standards
description: Documentation writing style guide for Mellea
category: docs
---
```

**Content guidance:**
- Use active voice, present tense
- Lead with what the user can DO, not what the feature IS
- Every page starts with a one-sentence purpose statement
- Code examples must be complete and runnable (include all imports)
- Use progressive disclosure: simple use case first, advanced options after
- Parameters documented in a table: name, type, default, description
- Return types documented explicitly
- Cross-reference using explicit file paths, never "see above" or "as mentioned"
- Heading hierarchy: H1 = page title, H2 = major sections, H3 = subsections
- No more than 3 heading levels per page
- Keep paragraphs under 4 sentences

---

#### Task 5.2.2 [skill] LLM readability skill

**File:** `skills/docs/llm-readability.md`

**Frontmatter:**
```yaml
---
name: llm-readability
description: What makes documentation LLM-friendly
category: docs
---
```

**Content guidance:**
- Self-contained pages: each page should be understandable without reading others
- Explicit over implicit: spell out types, defaults, and constraints
- Code examples include expected output (LLMs use input/output pairs for grounding)
- Avoid relative references ("the function above", "this module") — use full names
- Structured data in tables, not prose paragraphs
- API signatures in code blocks, not inline formatting
- One concept per page when possible
- Consistent naming: use the same term for the same concept everywhere
- Include "when to use" and "when NOT to use" sections for major features
- Error messages documented with cause and resolution

---

#### Task 5.2.3 [skill] Review criteria skill

**File:** `skills/docs/review-criteria.md`

**Frontmatter:**
```yaml
---
name: review-criteria
description: How to evaluate existing documentation quality
category: docs
---
```

**Content guidance:**

**Critical findings** (must fix):
- API signature in docs doesn't match actual code
- Code example has syntax errors or missing imports
- Feature documented but removed from codebase
- Broken cross-references or links

**Warning findings** (should fix):
- Missing code examples for documented features
- Parameters listed without types or defaults
- Prose that uses ambiguous pronouns or relative references
- Pages exceeding 500 lines without clear section breaks

**Info findings** (nice to fix):
- Missing "when to use" guidance
- Code examples without expected output
- Inconsistent terminology across pages
- Missing cross-references to related features

**Scoring:** Each finding has severity (critical/warning/info) and category
(stale_api, missing_example, broken_link, ambiguous_reference, etc.)

---

#### Task 5.2.4 [template] Docs update template

**File:** `templates/docs/update.j2`

**Structure:**
```
System: You are a technical documentation writer updating Mellea's docs based on recent changes.

{{ skills }}

Recent changes:
{{ context }}

Existing documentation for affected files:
{% for file in affected_files %}
### {{ file.path }}
{{ file.content }}
{% endfor %}

Task: Generate updated documentation for each affected file. For each file, output
the COMPLETE updated markdown content (not a diff). Preserve existing content that
is still accurate. Add, modify, or remove sections as needed based on the changes.

Output format:
For each file, use this structure:
```file:{{ "{" }}path{{ "}" }}
[complete updated markdown content]
```
```

---

#### Task 5.2.5 [template] Docs review checklist template

**File:** `templates/docs/review_checklist.j2`

**Structure:**
```
System: You are a documentation quality reviewer evaluating Mellea's docs for accuracy and LLM-readability.

{{ skills }}

Documentation to review:
{% for file in files %}
### {{ file.path }} ({{ file.size }} bytes)
{{ file.content }}
{% endfor %}

{% if api_surface %}
Current API surface for cross-checking:
{{ api_surface }}
{% endif %}

Task: Review each documentation file against the quality criteria. For each finding,
report:
- file_path: which file
- severity: critical, warning, or info
- category: stale_api, missing_example, broken_link, ambiguous_reference, missing_types, etc.
- description: what the issue is
- suggestion: how to fix it (optional)

Return findings as a JSON array. Be thorough but precise — false positives waste
reviewer time.
```

---

### Milestone 5.3: Docs Agents

#### Task 5.3.1 [code] Docs Writer agent

**File:** `agents/docs/__init__.py`

Empty init file.

**File:** `agents/docs/writer.py`

**SKILL_MANIFEST:**
```python
SKILL_MANIFEST = {
    "always": ["docs/writing-standards", "docs/llm-readability"],
    "conditional": {},
    "post_processing": [],
}
```

**`run()` signature:**
```python
def run(
    context_inputs: list[str],
    scope: str | None = None,
    no_cache: bool = False,
    dry_run: bool = False,
    stdout_only: bool = False,
) -> dict:
```

**Behavior:**
1. Resolve context via `resolve_context(context_inputs)` — typically a PR URL
   or release URL describing what changed.
2. Use LLM to identify affected doc files:
   - Call `llm.generate_structured(prompt, DocUpdatePlan)` with context
   - If `--scope` provided, constrain to that directory/file
3. Fetch existing content for affected files:
   - Use `GitHubClient.get_file_content()` for each file in the plan
   - If file doesn't exist yet (change_type="create"), pass empty content
4. Generate updated documentation:
   - Call `llm.generate_with_template("docs/update", ...)` with skills, context,
     and existing file contents
5. Parse output to extract per-file content (split on ````file:path```` markers)
6. If `dry_run` or `stdout_only`: print the generated docs to stdout
7. If not `dry_run`:
   - Create a branch (`{docs_branch_prefix}-{timestamp}`)
   - Commit updated files to the branch
   - Create a PR via `GitHubClient.create_pr()`
   - Print PR URL
8. Return dict with pr_number (or None), affected_files list, update_plan

**Agent name:** `"docs-writer"`

**Important:** The writer creates branches and PRs using PyGithub's git tree
and commit APIs rather than local git operations. This allows it to work in
CI/CD environments where the repo may be a shallow clone.

**Branch + commit via PyGithub:**
```python
def _create_branch_and_commit(
    self, client: GitHubClient, branch: str, files: dict[str, str], message: str
) -> None:
    """Create branch, commit files, using GitHub API (not local git)."""
    repo = client.repo
    default_branch = repo.default_branch
    ref = repo.get_git_ref(f"heads/{default_branch}")
    base_sha = ref.object.sha

    # Create branch
    repo.create_git_ref(f"refs/heads/{branch}", base_sha)

    # Create/update files on the branch
    for path, content in files.items():
        try:
            existing = repo.get_contents(path, ref=branch)
            repo.update_file(path, message, content, existing.sha, branch=branch)
        except Exception:
            repo.create_file(path, message, content, branch=branch)
```

---

#### Task 5.3.2 [code] Docs Reviewer agent

**File:** `agents/docs/reviewer.py`

**SKILL_MANIFEST:**
```python
SKILL_MANIFEST = {
    "always": ["docs/review-criteria", "docs/llm-readability"],
    "conditional": {},
    "post_processing": [],
}
```

**`run()` signature:**
```python
def run(
    scope: str | None = None,
    context_inputs: list[str] | None = None,
    no_cache: bool = False,
    stdout_only: bool = True,
    create_issues: bool = False,
) -> dict:
```

**Behavior:**
1. Discover documentation files to review:
   - Use `GitHubClient.get_tree(config.docs_target_dir)` to list all `.md` files
   - If `--scope` provided, filter to that path
2. Fetch content for each file:
   - Use `GitHubClient.get_file_content()` for each discovered file
   - Cap at 20 files per review (process in batches if needed)
3. Optionally build API surface context:
   - If `--context` provided, resolve it (e.g., a Python source directory)
   - This gives the reviewer reference material to check docs accuracy against
4. Generate review findings:
   - Call `llm.generate_structured(prompt, DocReviewReport)` with review checklist
     template, skills, and file contents
5. Format report:
   - Group findings by severity, then by file
   - Print summary counts and detailed findings
6. If `--create-issues`:
   - Create a GitHub issue for each critical finding
   - Title: `[Docs Review] {category}: {file_path}`
   - Body: finding description + suggestion
   - Labels: `docs-review`, `severity:{severity}`
7. If not `stdout_only`: save report via `save_draft()`
8. Return dict with files_reviewed, findings list, report text

**Agent name:** `"docs-reviewer"`

---

### Milestone 5.4: CLI Commands

#### Task 5.4.1 [code] CLI docs commands

**File:** `cli/commands/docs.py`

**Commands:**

```python
import typer
from typing import Annotated, Optional

app = typer.Typer(help="Documentation management commands")

@app.command()
def update(
    context: Annotated[
        list[str],
        typer.Option(
            "--context", "-c",
            help="PR URL, changelog, feature spec, or free text.",
        ),
    ] = [],
    scope: Annotated[
        Optional[str],
        typer.Option("--scope", "-s", help="Target docs directory or file path."),
    ] = None,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print changes without creating PR."),
    ] = False,
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print to stdout only."),
    ] = False,
) -> None:
    """Generate documentation updates from context and create a PR."""

@app.command()
def review(
    scope: Annotated[
        Optional[str],
        typer.Option("--scope", "-s", help="Docs directory or file to review."),
    ] = None,
    context: Annotated[
        list[str],
        typer.Option(
            "--context", "-c",
            help="API source code for accuracy cross-checking (optional).",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only/--save", help="Print to stdout (default) or save."),
    ] = True,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache."),
    ] = False,
    create_issues: Annotated[
        bool,
        typer.Option("--create-issues", help="Create GitHub issues for critical findings."),
    ] = False,
) -> None:
    """Review documentation quality and LLM-readability."""
```

**File:** `cli/main.py` (modify)

Add:
```python
from cli.commands import docs
app.add_typer(docs.app, name="docs")
```

---

### Milestone 5.5: GitHub Actions

#### Task 5.5.1 [infra] Release-triggered workflow

**File:** `.github/workflows/on_release.yml`

```yaml
name: DevRel on Release

on:
  release:
    types: [published]

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  devrel-content:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - name: Generate social posts
        env:
          DEVREL_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEVREL_GITHUB_REPO: ${{ github.repository }}
        run: |
          RELEASE_URL="${{ github.event.release.html_url }}"
          devrel content social --tone ibm --platform both --context "$RELEASE_URL" --save
          devrel content social --tone personal --platform both --context "$RELEASE_URL" --save
      - name: Generate technical blog draft
        env:
          DEVREL_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEVREL_GITHUB_REPO: ${{ github.repository }}
        run: |
          RELEASE_URL="${{ github.event.release.html_url }}"
          devrel content technical-blog --context "$RELEASE_URL"
      - name: Upload content drafts
        uses: actions/upload-artifact@v4
        with:
          name: content-drafts
          path: drafts/

  devrel-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - name: Update documentation
        env:
          DEVREL_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEVREL_GITHUB_REPO: ${{ github.repository }}
        run: |
          RELEASE_URL="${{ github.event.release.html_url }}"
          devrel docs update --context "$RELEASE_URL"
      - name: Review documentation
        env:
          DEVREL_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEVREL_GITHUB_REPO: ${{ github.repository }}
        run: |
          devrel docs review --create-issues
```

---

#### Task 5.5.2 [infra] Manual dispatch workflow

**File:** `.github/workflows/manual_dispatch.yml`

```yaml
name: DevRel Manual Dispatch

on:
  workflow_dispatch:
    inputs:
      workstream:
        description: "Workstream to run"
        required: true
        type: choice
        options:
          - content
          - monitor
          - demo
          - tracker
          - docs
      sub_agent:
        description: "Sub-agent (e.g., social, technical-blog, report, update, review)"
        required: true
        type: string
      context:
        description: "Context input (URL, text, etc.)"
        required: false
        type: string
      flags:
        description: "Additional flags (e.g., --tone personal --platform twitter)"
        required: false
        type: string

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - name: Run DevRel agent
        env:
          DEVREL_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEVREL_GITHUB_REPO: ${{ github.repository }}
        run: |
          CMD="devrel ${{ inputs.workstream }} ${{ inputs.sub_agent }}"
          if [ -n "${{ inputs.flags }}" ]; then
            CMD="$CMD ${{ inputs.flags }}"
          fi
          if [ -n "${{ inputs.context }}" ]; then
            CMD="$CMD --context \"${{ inputs.context }}\""
          fi
          eval $CMD
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: devrel-output
          path: |
            drafts/
            briefs/
```

---

### Milestone 5.6: Tests

#### Task 5.6.1 [test] Docs Writer agent tests

**File:** `tests/test_agents/test_docs_writer.py`

**Test cases:**
- `run()` with PR URL context identifies affected files via `generate_structured`
  (mock LLM returns `DocUpdatePlan`)
- Generated docs content is split correctly on ````file:path```` markers
- Dry run prints docs to stdout without creating branch/PR
- Non-dry-run creates branch and PR via GitHubClient (mock all GitHub calls)
- Scope flag limits affected files to specified path
- Skill manifest loads writing-standards + llm-readability

**Pattern:** Triple-patch (LLMClient, resolve_context, GitHubClient). Mock
`GitHubClient.get_file_content`, `GitHubClient.create_pr`, and the branch
creation helpers.

---

#### Task 5.6.2 [test] Docs Reviewer agent tests

**File:** `tests/test_agents/test_docs_reviewer.py`

**Test cases:**
- `run()` discovers and fetches docs files via `get_tree` + `get_file_content`
  (mock GitHubClient)
- Findings are structured as `DocReviewReport` via `generate_structured`
  (mock LLM)
- Scope flag filters which files are reviewed
- `--create-issues` creates GitHub issues for critical findings only
- stdout_only mode prints report without saving
- Missing docs directory handled gracefully (empty review)

**Pattern:** Mock GitHubClient for file discovery and LLMClient for review
generation.

---

#### Task 5.6.3 [test] GitHub Client tree/file tests

**File:** `tests/test_github_client.py` (modify)

**New test cases (from Task 5.0.3 — listed here for completeness):**
- `get_tree` returns list of file entries
- `get_file_content` returns decoded string
- `create_pr` returns PR number

---

#### Task 5.6.4 [test] CLI docs command tests

Verify CLI wiring by testing that commands call the correct agent functions.

**File:** `tests/test_agents/test_docs_cli.py`

**Test cases:**
- `update` command passes context, scope, dry_run, no_cache to writer agent
- `review` command passes scope, context, stdout_only, create_issues to reviewer
- docs typer is registered in main app

**Pattern:** Use `typer.testing.CliRunner` with mocked agent `run()` functions.

---

## Summary

| Milestone | Tasks | New Files | Modified Files |
|---|---|---|---|
| 5.0 Tech Debt | 3 | 0 | 1 |
| 5.1 Models + Config | 2 | 0 | 3 |
| 5.2 Skills + Templates | 5 | 5 | 0 |
| 5.3 Docs Agents | 2 | 3 | 0 |
| 5.4 CLI | 1 | 1 | 1 |
| 5.5 GitHub Actions | 2 | 2 | 0 |
| 5.6 Tests | 4 | 3 | 1 |
| **Total** | **19** | **14** | **6** |

## Dependencies

```
Milestone 5.0 (tech debt)          -- do first (get_tree/get_file_content/create_pr needed by 5.3)
Milestone 5.1 (models/config)      -- no dependency on 5.0, can parallel
Milestone 5.2 (skills/templates)   -- no dependency on 5.1, can parallel
   |
   +-- 5.0 + 5.1 + 5.2 must complete before 5.3
   |
Milestone 5.3 (agents)             -- depends on 5.0 (GitHub methods), 5.1 (models), 5.2 (skills)
Milestone 5.4 (CLI)                -- depends on 5.3 (agents exist)
Milestone 5.5 (GitHub Actions)     -- depends on 5.4 (CLI commands exist)
Milestone 5.6 (tests)              -- depends on 5.3 + 5.4
```

**Parallelizable:** 5.0, 5.1, and 5.2 can all be done in parallel.
5.3 follows after all three. 5.4 and 5.5 are sequential after 5.3.
5.6 follows last.

## Exit Criteria

- [ ] `devrel docs update --context "https://github.com/.../pull/123" --help` shows all flags
- [ ] `devrel docs update --context "URL" --dry-run` prints updated docs without creating PR
- [ ] `devrel docs update --context "URL"` creates a branch + PR with doc updates
- [ ] `devrel docs update --scope "docs/api" --context "URL"` limits scope to api docs
- [ ] `devrel docs review --help` shows scope, context, stdout-only, create-issues flags
- [ ] `devrel docs review` reports findings grouped by severity
- [ ] `devrel docs review --create-issues` creates GitHub issues for critical findings
- [ ] `devrel docs review --scope "docs/guides"` reviews only guide docs
- [ ] `get_tree` and `get_file_content` work on GitHub Client (tested)
- [ ] `create_pr` tested
- [ ] Release workflow fires on `release: published` event
- [ ] Manual dispatch workflow accepts workstream, sub_agent, context, flags inputs
- [ ] All tests pass (`pytest tests/ -q`)
- [ ] `ruff check .` passes with no errors

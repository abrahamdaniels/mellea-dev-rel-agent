# Mellea DevRel Agent System - Design Specification

**Date:** 2026-04-05 (updated 2026-04-07)
**Status:** Phase 6 Complete
**Author:** Architecture session with Abe

---

## 1. Problem Statement

The Mellea project (github.com/generative-computing/mellea) needs to scale its developer relations efforts across five workstreams: content creation, adoption monitoring, demonstration building, asset tracking, and documentation maintenance. A small team (2-4 people) currently handles this work manually. The goal is to automate 30-40% of this work through a family of specialized agents, built incrementally.

---

## 2. Design Principles

- **One agent, one generation task, one output format.** Agents that need to make routing decisions before doing their work should be split.
- **GitHub is the message bus.** Agents communicate through GitHub issues, PRs, and project board cards. No direct inter-agent messaging, no database, no custom state store.
- **Mellea for reliability, Python for orchestration.** Mellea handles structured output validation at the LLM call level (leaf-node injection pattern). Plain Python handles workflow coordination.
- **Universal context inputs.** Every agent that accepts context uses the same resolver. Build the parsing logic once.
- **Draft-first.** All generated content is a draft for human review. No auto-publishing to any platform.

---

## 3. System Architecture

### 3.1 Repo Structure

> **Note:** This reflects the actual state after Phase 6. All files listed below are implemented.

```
mellea-devrel/
  cli/
    __init__.py
    main.py                    # Unified `devrel` CLI entry point
    commands/
      __init__.py
      content.py               # Content workstream commands (social, technical-blog, suggest)
      monitor.py               # Monitor workstream commands (report, mentions)
      demo.py                  # Demo workstream commands (ideate, run, generate, test, package)
      tracker.py               # Asset tracker commands (log, sync)
      docs.py                  # Docs workstream commands  core/
    __init__.py
    context_resolver.py        # Universal context input parser (incl. brief: prefix)
    skill_loader.py            # Skill manifest resolver and file loader
    github_client.py           # GitHub API wrapper (issues, PRs, project board)
    llm_client.py              # LLM call wrapper with Mellea integration
    config.py                  # Configuration management (YAML + env vars + pydantic-settings + demo + tracker config)
    models.py                  # Shared Pydantic models (Phase 1-4: incl. TestResult, DemoConcept, AssetMetadata, AssetExtractionResult)
    output.py                  # Draft output utility (save_draft, stdout_only)
    briefs.py                  # Brief save/load for inter-agent intelligence feed
    pipeline.py                # Reusable pipeline engine with retry logic (Pipeline, StageResult)
    hooks.py                   # Post-hook system for fire-and-forget side effects
    mention_sources/
      __init__.py              # MentionSource ABC
      reddit.py                # Reddit public JSON API (3 subreddits)
      hackernews.py            # HN Algolia API (stories + comments)
      github_discussions.py    # GitHub GraphQL API
      pypi.py                  # PyPI JSON + pypistats API
      stackoverflow.py         # Stack Exchange API v2.3
      twitter.py               # Twitter/X v2 API (credential-gated)
      linkedin.py              # LinkedIn API (credential-gated placeholder)
      registry.py              # Explicit dict-based source registry
  agents/
    __init__.py
    content/
      __init__.py
      social_post.py           # Social post generation (personal + IBM)
      technical_blog.py        # HuggingFace-style technical blog
      suggest.py               # Content suggestion from monitor briefs
      blog_outline.py          # IBM Research blog skeleton
      personal_blog.py         # Personal blog, agnostic tone
    monitor/
      __init__.py              # Shared classify_sentiment helper
      report.py                # Weekly report generation with sentiment
      mentions.py              # Mention tracking with filtering
      publications.py          # Publication performance tracking
    demo/
      __init__.py              # parse_concept_file utility (:N selector)
      ideation.py              # Demo concept generation with brief loading
      code_gen.py              # Code generation with file extraction + repair context
      test_runner.py           # pytest harness (not an LLM agent)
      packager.py              # README generation + code polish + post-hook wiring
      pipeline.py              # Pipeline wiring: generate -> test -> package
    tracker/
      __init__.py              # Platform detection (detect_platform, infer_asset_type)
      log_asset.py             # Asset metadata extraction + GitHub issue creation
      sync.py                  # Reconcile untracked assets, report gaps
    docs/
      __init__.py
      writer.py                # Documentation creation/updates
      reviewer.py              # Documentation quality review
  skills/
    content/
      social-post.md           # How to write social posts (both tones)
      technical-blog.md        # HuggingFace-style technical blog instructions
      suggest.md               # Content opportunity identification and prioritization
      de-llmify.md             # Post-processing pass for all content
      twitter-conventions.md   # Twitter/X platform constraints and norms
      linkedin-conventions.md  # LinkedIn platform constraints and norms
      blog-outline.md          # IBM Research skeleton format
      personal-blog.md         # Personal blog guidelines
    monitor/
      weekly-report.md         # How to structure the weekly report
      sentiment-scoring.md     # How to classify sentiment
      mention-evaluation.md    # How to assess mention relevance
      publications-tracking.md # Publication performance evaluation
    demo/
      ideation.md              # How to generate demo concepts
      code-generation.md       # Code quality standards and patterns
      packaging.md             # README and polish standards
    tracker/
      asset-extraction.md      # How to extract metadata from assets
      issue-formatting.md      # GitHub issue structure for tracked assets
    docs/
      writing-standards.md     # Documentation style guide
      llm-readability.md       # What makes docs LLM-friendly
      review-criteria.md       # How to evaluate existing docs
    shared/
      mellea-knowledge.md      # What Mellea is, key features, API surface
      tone-ibm.md              # IBM tone and messaging guidelines
      tone-personal.md         # Personal/agnostic tone guidelines
  templates/
    content/
      social_post.j2           # Social post prompt template (both tones)
      technical_blog.j2        # HuggingFace blog prompt template
      suggest.j2               # Content suggestion prompt template
      blog_outline.j2          # IBM Research outline prompt template
      personal_blog.j2         # Personal blog prompt template
    monitor/
      weekly_report.j2         # Weekly report prompt template
      publications_report.j2   # Publications performance report template
    demo/
      concept.j2               # Demo concept prompt template
      code_gen.j2              # Demo code generation prompt template
      readme.j2                # Demo README prompt template
    tracker/
      issue_body.j2            # GitHub issue template for tracked assets
    docs/
      review_checklist.j2      # Docs review criteria prompt template
      update.j2                # Docs update prompt template
  tests/
    __init__.py
    test_config.py
    test_context_resolver.py
    test_skill_loader.py
    test_github_client.py
    test_llm_client.py
    test_output.py
    test_briefs.py
    test_pipeline.py
    test_hooks.py
    test_agents/
      __init__.py
      test_social_post.py
      test_technical_blog.py
      test_monitor_report.py
      test_monitor_mentions.py
      test_content_suggest.py
      test_demo_init.py
      test_demo_ideation.py
      test_demo_code_gen.py
      test_demo_test_runner.py
      test_demo_packager.py
      test_demo_pipeline.py
      test_tracker_init.py
      test_tracker_log_asset.py
      test_tracker_sync.py
      test_docs_writer.py
      test_docs_reviewer.py
      test_blog_outline.py
      test_personal_blog.py
      test_monitor_publications.py
    test_mention_sources/
      __init__.py
      test_reddit.py
      test_hackernews.py
      test_pypi.py
      test_registry.py
      test_github_discussions.py
      test_stackoverflow.py
      test_twitter.py
      test_linkedin.py
    fixtures/
      __init__.py
  .github/
    workflows/
      ci.yml                   # Push/PR trigger, Python 3.11+3.12 matrix, ruff + pytest
      monitor_weekly.yml       # Scheduled weekly monitor run (Mon 9am UTC) + manual dispatch
      on_release.yml           # Trigger docs + content on new release
      manual_dispatch.yml      # Manual trigger for any workstream
  pyproject.toml
  config.yml
  .env.example
  .gitignore
```

### 3.2 Layer Diagram

```
+-------------------------------------------------------+
|                   CLI Layer (Typer)                     |
|   devrel <workstream> <sub-agent> [--flags]            |
+-------------------------------------------------------+
                          |
+-------------------------------------------------------+
|                   Core Layer                            |
| Context Resolver | Skill Loader | GitHub Client | LLM  |
+-------------------------------------------------------+
                    |              |
+-------------------+--------------+--------------------+
|    Agent Layer    |   Skill Layer (markdown)           |
|  12 specialized   |   Declarative instructions,        |
|  Python units     |   rubrics, checklists, formats     |
|  (10 LLM + 1      |   loaded per-invocation via        |
|   router + 1      |   skill manifests                  |
|   test runner)    |                                    |
+-------------------+-----------------------------------+
                          |
+-------------------------------------------------------+
|                   Template Layer (Jinja2)               |
|  Prompt assembly: skill content + context + variables  |
+-------------------------------------------------------+
                          |
+-------------------------------------------------------+
|                   Output Layer                          |
|  GitHub Issues/PRs | Markdown files | stdout drafts    |
+-------------------------------------------------------+
```

### 3.3 Skills vs Templates vs Agent Code

These three layers have distinct responsibilities:

- **Skill files** (markdown) define *what* to do: instructions, quality criteria, scoring rubrics, output formats, and common mistakes. They are the agent's domain knowledge. Changing a skill changes the agent's behavior without touching code.
- **Templates** (Jinja2) define *how to assemble the prompt*: they stitch together skill content, resolved context, and agent-specific variables into the final prompt string sent to the LLM.
- **Agent code** (Python) defines *the mechanics*: CLI parsing, context resolution, skill loading, LLM calls with Mellea validation, and output writing. This code changes rarely once built.

---

## 4. Core Components

### 4.1 Context Resolver

The Context Resolver is the most important shared component. It normalizes all input types into a unified context block that any agent can consume.

**Input types detected automatically:**

| Input | Detection | Fetching |
|---|---|---|
| GitHub PR URL | Regex match on `github.com/.../pull/\d+` | GitHub API: title, description, diff, comments |
| GitHub Issue URL | Regex match on `github.com/.../issues/\d+` | GitHub API: title, body, labels, comments |
| GitHub Release URL | Regex match on `github.com/.../releases/...` | GitHub API: tag, body, assets |
| Web URL | Any `http://` or `https://` not matching GitHub patterns | HTTP fetch + HTML-to-markdown extraction |
| Local file path | Exists on filesystem | Read file, detect type (markdown, python, json, etc.) |
| Raw text | Everything else (no URL pattern, no file match) | Pass through as-is |

**Output format:**

```python
@dataclass
class ContextBlock:
    sources: list[ContextSource]
    combined_text: str          # All sources concatenated with headers
    metadata: dict              # PR numbers, file types, URLs for reference

@dataclass
class ContextSource:
    source_type: str            # "github_pr", "github_issue", "web", "file", "text"
    origin: str                 # Original input string
    title: str | None           # PR title, page title, filename
    content: str                # Extracted/fetched content
    metadata: dict              # Type-specific metadata (diff stats, labels, etc.)
```

**CLI usage:**

```bash
# Single GitHub PR
devrel content technical-blog --context "https://github.com/.../pull/676"

# Multiple mixed inputs
devrel content social --tone personal \
  --context "https://github.com/.../pull/676" \
  --context "./notes.md" \
  --context "This enables streaming for all backends"
```

The `--context` flag is repeatable. Each value is resolved independently, then all are combined into a single `ContextBlock` for the target agent.

### 4.2 GitHub Client

Wraps PyGithub for all GitHub operations used across agents:

- **Read:** Fetch PR details, issue bodies, release notes, repo stats (stars, forks, traffic)
- **Write:** Create issues, add issues to project board, create PRs, update issue labels
- **Project Board:** Add cards with custom fields (asset type, feature, date, sentiment, link)

Configuration via environment variables:

```
DEVREL_GITHUB_TOKEN=ghp_...
DEVREL_GITHUB_REPO=generative-computing/mellea
DEVREL_GITHUB_PROJECT_ID=<project board ID>
```

### 4.3 LLM Client

A thin wrapper that provides a consistent interface for all agents to make LLM calls. Integrates Mellea for structured output validation where it adds value.

```python
class LLMClient:
    def generate(self, prompt: str, template: str | None = None,
                 context: ContextBlock | None = None) -> str:
        """Simple text generation."""

    def generate_structured(self, prompt: str, output_type: type[BaseModel],
                            requirements: list | None = None,
                            context: ContextBlock | None = None) -> BaseModel:
        """Structured output with Mellea validation."""
```

The `generate_structured` method uses Mellea's `@generative` or `instruct(format=...)` pattern with requirements and rejection sampling. This is where Mellea's reliability layer adds the most value: ensuring social posts meet character limits, blog outlines have required sections, demo code parses correctly, etc.

**Model configuration:**

```yaml
# config.yml
llm:
  default_backend: "ollama"        # or "openai", "anthropic", etc.
  default_model: "granite-3.3-8b"  # configurable per environment
  overrides:
    code_gen: "granite-3.3-8b"     # can override per agent
    sentiment: "granite-3.3-2b"    # lighter model for classification
```

### 4.4 Skill System

Skills are markdown instruction files that define what an agent does and how it evaluates quality. They are the agent's domain knowledge, separated from the execution mechanics in Python code. This separation means you can change an agent's behavior by editing a markdown file without touching code.

#### Skill file structure

Every skill file follows a consistent format:

```markdown
---
name: social-post
description: >-
  How to write social media posts for Twitter/X and LinkedIn
  promoting Mellea features. Covers both personal and IBM tones.
applies_to: [content]
---

# Skill Title

One paragraph on when this skill applies and what it produces.

## Steps

Numbered, sequential instructions the agent follows.

## Decision Tables

Where the agent needs to make judgment calls (tone, format, scoring).

## Output Format

Exact structure of what the agent produces, with a template or example.

## Self-Review Checklist

Quality gates the agent checks before finalizing output.

## Common Mistakes

What to avoid. These are surprisingly effective at improving output quality.

## Related Skills

Cross-references to skills that pair well with this one.
```

Not every section is required for every skill. Simple skills (like `twitter-conventions.md`) may only have a few sections. Complex skills (like `technical-blog.md`) use all of them.

#### Skill manifests

Each agent declares a skill manifest at the top of its Python file. The manifest defines which skills are always loaded, which are loaded conditionally based on CLI flags, and which run as post-processing passes.

```python
# agents/content/social_post.py

SKILL_MANIFEST = {
    "always": [
        "content/social-post",
        "shared/mellea-knowledge",
    ],
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
    "post_processing": [
        "content/de-llmify",
    ],
}
```

When the user runs `devrel content social --tone personal --platform twitter`, the Skill Loader resolves the manifest against the provided flags and produces the exact set of skills needed for this invocation:

1. `content/social-post` (always)
2. `shared/mellea-knowledge` (always)
3. `shared/tone-personal` (matched `--tone personal`)
4. `content/twitter-conventions` (matched `--platform twitter`)

After generation, `content/de-llmify` runs as a post-processing pass.

Skills that don't match any provided flag are not loaded. The agent never sees instructions it doesn't need.

#### Skill Loader (core/skill_loader.py)

The Skill Loader is a small utility in the core layer that resolves manifests:

```python
from pathlib import Path

SKILLS_DIR = Path("skills")

def resolve_manifest(manifest: dict, flags: dict) -> list[Path]:
    """Resolve a skill manifest against CLI flags.
    Returns ordered list of skill file paths to load."""
    paths = []

    for skill_name in manifest.get("always", []):
        paths.append(SKILLS_DIR / f"{skill_name}.md")

    for flag_name, options in manifest.get("conditional", {}).items():
        flag_value = flags.get(flag_name)
        if flag_value and flag_value in options:
            paths.append(SKILLS_DIR / f"{options[flag_value]}.md")

    return paths

def resolve_post_processing(manifest: dict) -> list[Path]:
    """Return post-processing skill paths."""
    return [SKILLS_DIR / f"{s}.md" for s in manifest.get("post_processing", [])]

def load_skill_content(paths: list[Path]) -> str:
    """Read and concatenate skill files, stripping YAML frontmatter."""
    sections = []
    for path in paths:
        text = path.read_text()
        # Strip YAML frontmatter
        if text.startswith("---"):
            end = text.index("---", 3)
            text = text[end + 3:].strip()
        sections.append(text)
    return "\n\n---\n\n".join(sections)
```

#### How skills flow into prompts

The prompt assembly pipeline for any agent invocation:

```
1. CLI parses flags
2. Context Resolver fetches and normalizes --context inputs
3. Skill Loader resolves manifest against flags -> list of skill files
4. Skill content is loaded and concatenated
5. Jinja2 template assembles: skill content + context block + agent variables
6. LLM Client sends the assembled prompt (with Mellea validation if applicable)
7. If post-processing skills exist, output is passed through them as a second LLM call
```

#### Complete agent example

Here is how the Social Post agent uses the skill system end-to-end:

```python
# agents/content/social_post.py

from core.skill_loader import resolve_manifest, resolve_post_processing, load_skill_content
from core.context_resolver import resolve_context
from core.llm_client import LLMClient

SKILL_MANIFEST = {
    "always": [
        "content/social-post",
        "shared/mellea-knowledge",
    ],
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
    "post_processing": [
        "content/de-llmify",
    ],
}

def run(context_inputs: list[str], tone: str, platform: str) -> str:
    flags = {"tone": tone, "platform": platform}

    # 1. Resolve context
    context = resolve_context(context_inputs)

    # 2. Load skills for this invocation
    skill_paths = resolve_manifest(SKILL_MANIFEST, flags)
    skill_content = load_skill_content(skill_paths)

    # 3. Generate
    client = LLMClient()
    draft = client.generate(
        template="content/social_post.j2",
        variables={
            "skills": skill_content,
            "context": context.combined_text,
            "tone": tone,
            "platform": platform,
        },
    )

    # 4. Post-process
    pp_paths = resolve_post_processing(SKILL_MANIFEST)
    if pp_paths:
        pp_content = load_skill_content(pp_paths)
        draft = client.generate(
            template="content/post_process.j2",
            variables={
                "skills": pp_content,
                "draft": draft,
            },
        )

    return draft
```

#### Skill manifests for all agents

| Agent | Always | Conditional | Post-processing |
|---|---|---|---|
| Social Post | social-post, mellea-knowledge | tone: personal/ibm, platform: twitter/linkedin | de-llmify |
| Technical Blog | technical-blog, mellea-knowledge | (none) | de-llmify |
| Blog Outline | blog-outline, mellea-knowledge | (none) | (none) |
| Personal Blog | personal-blog, mellea-knowledge | (none) | de-llmify |
| Monitor Report | weekly-report, sentiment-scoring | source-specific: mention-evaluation | (none) |
| Mention Check | mention-evaluation, sentiment-scoring | (none) | (none) |
| Demo Ideation | ideation, mellea-knowledge | (none) | (none) |
| Demo Code Gen | code-generation, mellea-knowledge | (none) | (none) |
| Demo Packager | packaging, mellea-knowledge | (none) | (none) |
| Asset Logger | asset-extraction, issue-formatting | (none) | (none) |
| Docs Writer | writing-standards, llm-readability | (none) | (none) |
| Docs Reviewer | review-criteria, llm-readability | (none) | (none) |

### 4.5 Config

YAML-based configuration with environment variable overrides:

```yaml
github:
  repo: "generative-computing/mellea"
  project_board_id: "PVT_..."
  token_env: "DEVREL_GITHUB_TOKEN"

monitor:
  mention_sources:
    - reddit
    - hackernews
    - twitter
    - github_discussions
  publication_locations:
    - twitter
    - linkedin
    - huggingface
    - ibm_research
  schedule: "weekly"              # default cadence

content:
  default_tone: "personal"
  social_char_limit: 280          # Twitter limit
  linkedin_char_limit: 3000
```

---

## 5. Agent Communication

Agents communicate through three patterns, chosen based on the type of interaction.

### 5.1 Pipeline Chaining

For multi-stage workflows where one agent's output feeds directly into the next agent's input. The pipeline runs as a single command and handles stage-to-stage data passing, failure detection, and retry logic.

**Currently used by:** Demo pipeline (generate -> test -> package)

```python
# core/pipeline.py

from dataclasses import dataclass

@dataclass
class StageResult:
    stage_name: str
    success: bool
    output: dict          # Passed as input to the next stage
    error_context: str | None  # Fed back on retry

class Pipeline:
    def __init__(self, stages: list[tuple[str, callable]],
                 on_stage_failure: dict | None = None):
        self.stages = stages
        self.on_stage_failure = on_stage_failure or {}

    def run(self, initial_input: dict) -> list[StageResult]:
        """Run all stages sequentially."""
        results = []
        current_input = initial_input

        for stage_name, stage_fn in self.stages:
            result = stage_fn(**current_input)

            if not result.success and stage_name in self.on_stage_failure:
                failure_config = self.on_stage_failure[stage_name]
                result = self._handle_failure(
                    stage_name, stage_fn, result, current_input, failure_config
                )

            if not result.success:
                results.append(result)
                break  # Stop pipeline on unrecoverable failure

            results.append(result)
            current_input = result.output

        return results

    def _handle_failure(self, stage_name, stage_fn, result,
                        previous_input, config) -> StageResult:
        """Retry the previous stage with failure context."""
        if config["action"] == "retry_previous":
            prev_name, prev_fn = self._get_previous_stage(stage_name)
            for attempt in range(config["retry_budget"]):
                repair_input = {
                    **previous_input,
                    "repair_context": result.error_context,
                    "attempt": attempt + 1,
                }
                prev_result = prev_fn(**repair_input)
                if prev_result.success:
                    # Re-run the failing stage with new output
                    retry_result = stage_fn(**prev_result.output)
                    if retry_result.success:
                        return retry_result
                    result = retry_result  # Update error for next retry
        return result  # All retries exhausted
```

Pipelines are only used when stages have a clear sequential dependency and the
handoff is fully automated. If a human approval gate exists (like between demo
ideation and generation), the stages on either side of the gate are separate
commands, not part of the same pipeline.

### 5.2 Post-Hooks (Fire-and-Forget Side Effects)

For actions that should happen automatically after an agent runs, without the
agent needing to know about them. Hooks are best-effort: if they fail, the
primary agent's output is unaffected.

```python
# core/hooks.py

POST_HOOKS = {
    "demo.packager": [
        "tracker.log_asset",  # Completed demos auto-log to project board
    ],
}

def run_post_hooks(agent_name: str, agent_output: dict):
    for pattern, hooks in POST_HOOKS.items():
        if matches(agent_name, pattern):
            for hook in hooks:
                try:
                    invoke_agent(hook, context=agent_output)
                except Exception as e:
                    logger.warning(f"Post-hook {hook} failed: {e}")
```

**Content agents have no post-hooks.** Content agents produce drafts. Only
published content should be tracked, and publishing is a manual action. Asset
tracking for published content is user-initiated via `devrel tracker log`.

Hooks can be disabled per-invocation with `--no-hooks` for debugging or
when running agents in isolation.

### 5.3 Intelligence Feeds (Monitor -> Content)

The monitor agent produces structured intelligence that content agents can
consume as context input. This is a publish-subscribe pattern using the
filesystem: the monitor writes, other agents read when they choose to.

**How it works:**

1. Monitor agent runs (weekly or on-demand) and saves structured output:

```
briefs/
  latest-weekly-report.json
  latest-mentions.json
  latest-trending-topics.json
```

2. Any agent can read a brief as context using the `brief:` prefix:

```bash
devrel content social --tone personal --context brief:trending-topics
```

3. The Context Resolver handles the `brief:` prefix by reading the
   corresponding file from the briefs directory:

```python
# In context_resolver.py
if input_str.startswith("brief:"):
    brief_name = input_str.split(":", 1)[1]
    path = BRIEFS_DIR / f"latest-{brief_name}.json"
    return ContextSource(
        source_type="brief",
        origin=input_str,
        title=brief_name,
        content=path.read_text(),
        metadata={"brief_date": get_brief_date(path)},
    )
```

4. A dedicated `suggest` sub-agent reads monitor briefs and proposes
   content ideas:

```bash
# "What should I write about this week?"
devrel content suggest
# Reads latest monitor brief + recent GitHub releases
# Outputs a prioritized list of content opportunities
```

The monitor does not call content agents. It publishes data. Content agents
consume it when the user decides to.

### 5.4 Communication Map

```
                    Monitor
                      |
                      | writes briefs
                      v
                  briefs/*.json
                      |
          +-----------+-----------+
          |                       |
          v                       v
   Content Suggest          (any agent can
   (reads briefs,            read briefs as
    proposes topics)          --context brief:X)
          |
          v
    Content Agents                Asset Tracker
    (social, blog,      <-- user-initiated -->
     outline, etc.)       devrel tracker log
    produce drafts        --context "live URL"

    Demo Pipeline:
    Ideation --> [HUMAN APPROVAL] --> Generate --> Test --> Package
                                      |                |     |
                                      +-- on failure --+     |
                                                             v
                                                    post-hook: tracker

    Docs Writer <--- triggered by ---> GitHub Release event
    Docs Reviewer --- runs on schedule ---> GitHub Issues
```

---

## 6. Agent Specifications

### 6.1 Content Workstream

**Router:** The CLI command `devrel content <sub-agent>` routes directly to the target agent. No LLM-based routing needed; the user specifies what they want.

#### 6.1.1 Social Post Agent

**Input:** `--context` (any type) + `--tone` (personal | ibm) + `--platform` (twitter | linkedin | both)
**Output:** Draft post(s) written to stdout and optionally saved to a markdown file.

**Behavior:**
- Reads context via Context Resolver
- Selects prompt template based on tone flag
- Generates platform-appropriate drafts (respects character limits)
- If `--platform both`, generates one draft per platform
- Uses Mellea requirements to enforce: character limits, no hallucinated features, tone alignment

**Mellea integration:**
```python
@generative
def generate_social_post(
    context_summary: str,
    tone: Literal["personal", "ibm"],
    platform: Literal["twitter", "linkedin"]
) -> SocialPost:
    """Generate a social media post about a Mellea feature or update."""
```

With requirements:
- Character limit validation (simple_validate)
- No URLs in body unless provided in context
- Tone check (IBM posts must not use first person singular)

#### 6.1.2 Technical Blog Agent

**Input:** `--context` (typically a PR URL or feature spec)
**Output:** Full markdown blog post with code examples, saved to file.

**Behavior:**
- Fetches PR diff and description via Context Resolver
- Generates a HuggingFace-audience blog: problem statement, walkthrough, code examples, conclusion
- Code examples must be runnable (validated in a later manual or automated step)
- Output includes frontmatter for HuggingFace blog format

**Mellea integration:**
- Requirements: code blocks must be valid Python (syntax check), must reference actual Mellea APIs, must include imports
- Structured output for blog metadata (title, tags, summary)

#### 6.1.3 Blog Outline Agent

**Input:** `--context` (feature info, PR, or free text)
**Output:** Structured outline in markdown, saved to file.

**Behavior:**
- Produces an IBM Research blog skeleton with sections: What It Is, Why It Matters, How To Use It
- No full prose, just section headers with 2-3 bullet points each
- Includes suggested title options and target audience note

#### 6.1.4 Personal Blog Agent

**Input:** `--context` (any type)
**Output:** Full markdown blog post, agnostic tone, saved to file.

**Behavior:**
- Similar structure to technical blog but without IBM alignment
- More conversational tone permitted
- Can include personal opinions and broader ecosystem commentary

#### 6.1.5 Content Suggest Agent (`devrel content suggest`)

**Input:** None required (reads latest monitor briefs automatically). Optional `--context` for additional focus.
**Output:** Prioritized list of content opportunities to stdout.

**Behavior:**
- Reads the latest monitor briefs from `briefs/` directory (trending topics, recent mentions, sentiment data)
- Cross-references with recent GitHub releases and merged PRs
- Identifies content gaps: features shipped but not written about, trending topics with no Mellea angle yet, high-engagement areas worth doubling down on
- Produces a ranked list of content ideas with recommended format (social post, blog, demo) and suggested tone (personal vs IBM)

**This agent bridges the monitor and content workstreams.** It consumes monitor intelligence and produces actionable content recommendations. It does not generate content itself.

**Output format:**

```markdown
# Content Suggestions - {date}

Based on this week's monitor data and recent project activity.

## Top Opportunities

### 1. {topic}
**Why now:** {what triggered this - trending mention, new release, sentiment shift}
**Recommended format:** {social post | technical blog | blog outline | demo}
**Recommended tone:** {personal | ibm}
**Context to use:** {PR URL, mention link, or brief reference}

### 2. {topic}
...
```

---

### 6.2 Monitor Workstream

**Single agent** with sub-commands for different report types.

#### 6.2.1 Full Report (`devrel monitor report`)

**Input:** `--source` (optional, filters to specific platforms)
**Output:** Markdown report written to file + summary to stdout.

**Data collected:**

Quantitative (via APIs):
- GitHub: stars, forks, open issues, PR velocity, contributor count
- PyPI: download counts (daily, weekly, monthly trends)
- GitHub traffic: views, clones, referral sources

Qualitative (via search/scraping):
- Reddit mentions (r/MachineLearning, r/LocalLLaMA, r/Python)
- Hacker News mentions
- Twitter/X mentions and sentiment
- GitHub Discussions activity and sentiment

Publication tracking:
- Assets logged via Tracker agent (cross-referenced from project board)
- Which platforms received content this period
- Engagement metrics where available

**Report structure:**
```markdown
# Mellea DevRel Weekly Report - {date}

## Metrics Snapshot
- Stars: {n} (+{delta})
- PyPI Downloads (7d): {n} (+{delta}%)
- Open Issues: {n}

## Mention Activity
| Source | Count | Sentiment | Notable |
| ...

## Publication Activity
| Asset | Platform | Date | Link |
| ...

## Highlights and Recommendations
- {LLM-generated summary of notable trends}
- {Suggested actions based on data}
```

**Mellea integration:**
- Sentiment classification using `@generative` with `Literal["positive", "negative", "neutral", "mixed"]`
- Report summary generation with requirements (must reference specific data points, no fabricated numbers)

#### 6.2.2 Mention Check (`devrel monitor mentions`)

**Input:** `--source` (reddit | hackernews | twitter | github_discussions)
**Output:** List of recent mentions with sentiment to stdout.

Lighter-weight than the full report. Just fetches and classifies recent mentions from the specified source.

---

### 6.3 Demo Workstream

Two-phase workflow with a human approval gate between ideation and execution.

**Phase 1: Ideation (standalone, always manual)**

The ideation agent proposes demo concepts. A human reviews and selects one.

**Phase 2: Execution pipeline (automated, chained)**

Once a concept is approved, the generate -> test -> package stages run as an
automated pipeline. If tests fail, the pipeline retries code generation with
the failure output as repair context.

```
Ideation --> [HUMAN APPROVAL GATE] --> Generate --> Test --> Package
                                       |                |
                                       +-- on failure --+
                                       (retry with error context,
                                        up to 2 retries)
```

**CLI usage:**

```bash
# Phase 1: Generate concepts (always standalone)
devrel demo ideate --context "https://github.com/.../pull/676"
# Output: drafts/demo-concepts-2026-04-05.md

# You review the concepts file, pick concept #2

# Phase 2: Run the automated pipeline from generate onward
devrel demo run --concept ./drafts/demo-concepts-2026-04-05.md:2 --context "..."

# Or run individual stages manually when needed
devrel demo generate --concept "..." --context "..."
devrel demo test --path ./demos/streaming_demo/
devrel demo package --path ./demos/streaming_demo/
```

**Pipeline implementation:**

```python
# agents/demo/pipeline.py

from core.pipeline import Pipeline

DEMO_PIPELINE = Pipeline(
    stages=[
        ("generate", code_gen.run),
        ("test", test_runner.run),
        ("package", packager.run),
    ],
    on_stage_failure={
        "test": {
            "action": "retry_previous",   # loop back to generate
            "retry_budget": 2,            # max 2 retries
            "feed_output": True,          # pass failure output as context
        },
    },
)
```

When tests fail, the pipeline feeds the test output (error messages, stack traces,
failing assertions) back to the code gen agent as additional context. The code gen
agent regenerates with both the original concept and the failure information. This
is Mellea's instruct-validate-repair pattern applied at the pipeline level.

If the retry budget is exhausted, the pipeline stops and reports the failures
so the human can intervene.

#### 6.3.1 Ideation Agent (`devrel demo ideate`)

**Input:** `--context` (feature description, trending project URL, model card, or free text)
**Output:** 3-5 demo concepts with descriptions, saved to markdown file.

**Behavior:**
- Analyzes the provided context
- Proposes demo concepts that showcase Mellea's value
- Each concept includes: title, description, target audience, estimated complexity, key Mellea features used

**Output format:**

```markdown
# Demo Concepts - {date}

**Source:** {context summary}

---

## Concept 1: {title}

**Description:** {2-3 sentences}
**Target audience:** {who this demo is for}
**Complexity:** {S | M | L}
**Mellea features:** {list of specific features used}
**Why this works:** {1 sentence on why this concept is compelling}

---

## Concept 2: {title}
...
```

The `:N` suffix on the concept file path (e.g., `./drafts/demo-concepts.md:2`)
tells the pipeline to extract concept N from the file. The pipeline parser reads
the markdown, splits on `## Concept N` headers, and passes the selected concept
to the generate stage.

#### 6.3.2 Code Generation Agent (`devrel demo generate`)

**Input:** `--concept` (description or path to concept file) + `--context` (optional additional context) + `--repair-context` (optional, injected by pipeline on retry)
**Output:** Python files for the demo, saved to a directory.

**Behavior:**
- Takes a single demo concept and produces runnable code
- Generates: main script, any helper modules, requirements.txt, test file
- Code must use actual Mellea APIs (validated against known API surface)
- Includes inline comments explaining each step
- On retry: receives previous test failures as `--repair-context` and adjusts the generated code to fix the specific issues

**Mellea integration:**
- Requirements: valid Python syntax, imports resolve, uses real Mellea APIs
- Rejection sampling with budget of 3 to get parseable code

**Generated test file:**

The code gen agent also produces a basic test file (`test_demo.py`) that the
test runner will execute. This test file should:
- Import the main module without error
- Call the primary function with sample input
- Assert the output type matches expectations
- Check that no exceptions are raised during normal execution

#### 6.3.3 Test Runner (`devrel demo test`)

**Input:** `--path` (directory containing generated demo)
**Output:** Structured test result (pass/fail, error details, stdout/stderr).

**Not an LLM agent.** This is a pytest harness that:
- Creates a virtual environment
- Installs dependencies from requirements.txt + mellea
- Runs any test files in the demo directory via pytest
- Returns structured output the pipeline can use for retry decisions

If no test file exists, it runs a basic smoke test: import the main module,
check for syntax errors, verify imports resolve.

**Structured output for pipeline consumption:**

```python
@dataclass
class TestResult:
    passed: bool
    total_tests: int
    failed_tests: int
    error_output: str | None    # stderr + pytest output, fed back to code gen on retry
    failing_test_names: list[str]
```

#### 6.3.4 Packager Agent (`devrel demo package`)

**Input:** `--path` (directory containing passing demo)
**Output:** Polished demo directory with README.md, cleaned code, usage instructions.

**Behavior:**
- Reads the generated code
- Produces a README with: overview, prerequisites, usage instructions, expected output, explanation of Mellea features used
- Cleans up code formatting and comments
- Adds license header if needed

**Only runs if tests pass.** The pipeline enforces this. If you run `devrel demo package` manually on a directory that hasn't been tested, it prints a warning but proceeds.

---

### 6.4 Asset Tracker Workstream

**Single agent** for logging and syncing. Triggered in two ways:

- **User-initiated** for published content (blog posts, social posts, articles). You publish manually, then run `devrel tracker log` with the live URL.
- **Automated via post-hook** for completed demos. When the demo pipeline finishes packaging, the tracker is called automatically.

This distinction exists because content agents produce drafts, not published assets. Only content that is actually published should be tracked. Demos, by contrast, are finished artifacts in the repo once they pass tests and get packaged.

#### 6.4.1 Log Asset (`devrel tracker log`)

**Input:** `--context` (URL to published asset) + optional explicit flags: `--type` (blog | social_post | ibm_article | demo | talk) + `--title` + `--link` + `--feature`
**Output:** GitHub issue created on project board.

**Typical usage after publishing:**

```bash
# You just posted a tweet about the new streaming API
devrel tracker log --context "https://twitter.com/you/status/123456789"

# The tracker fetches the tweet, extracts metadata automatically:
# - Type: social_post (inferred from twitter.com URL)
# - Title: extracted from tweet text
# - Feature: extracted via LLM from tweet content
# - Sentiment: classified via LLM
# - Location: the provided URL
# - Date: today
```

**Behavior:**
- If `--context` is a URL to a published asset, auto-extracts all metadata
- If explicit flags are provided, uses those directly (overrides auto-extraction)
- Creates a GitHub issue with structured body:

```markdown
## Asset Tracking

| Field | Value |
|---|---|
| Type | {type} |
| Feature | {feature} |
| Title | {title} |
| Date | {date} |
| Sentiment | {sentiment} |
| Location | {link} |
```

- Adds issue to the GitHub Project board with custom fields matching the table above
- Applies labels: `asset-tracking`, `type:{type}`

**Mellea integration:**
- Sentiment analysis of the asset content using `@generative` with Literal return type
- Auto-extraction of title/feature from context when not explicitly provided
- Platform detection from URL pattern (twitter.com -> social_post, huggingface.co -> blog, etc.)

#### 6.4.2 Sync (`devrel tracker sync`)

**Input:** None (scans for untracked assets)
**Output:** Report of assets found but not tracked, with option to log them.

Scans known publication locations and cross-references against existing project board entries. Flags gaps. This is a safety net for assets you forgot to log manually.

---

### 6.5 Docs Workstream

Two agents with distinct roles.

#### 6.5.1 Writer Agent (`devrel docs update`)

**Input:** `--context` (PR URL, changelog, feature spec, or free text) + `--scope` (optional, target docs directory)
**Output:** PR with documentation updates.

**Behavior:**
- Reads the context (e.g., a merged PR that changed an API)
- Identifies which documentation files are affected
- Generates updated markdown for those files
- Creates a GitHub PR with the changes for team review

**Mellea integration:**
- Requirements: updated docs must reference actual API signatures, must not remove existing content without justification
- Structured output for identifying affected files

#### 6.5.2 Reviewer Agent (`devrel docs review`)

**Input:** `--scope` (optional, target docs directory or file)
**Output:** Review report as markdown to stdout + optional GitHub issue for each finding.

**Behavior:**
- Reads existing documentation
- Evaluates against LLM-readability criteria:
  - Are code examples complete and runnable?
  - Are API signatures current?
  - Is the structure parseable by an LLM (clear headers, consistent formatting)?
  - Are there gaps where features exist but docs don't?
- Produces a prioritized list of findings

**Review criteria for LLM-readability:**
- Each page has a clear title and purpose statement
- Code examples include all necessary imports
- Parameters and return types are documented
- Cross-references use explicit paths, not relative pronouns ("see the section above")
- No ambiguous pronouns or references that require page-level context to resolve

---

## 7. GitHub Actions Integration

Three workflow files cover all automation scenarios:

### 7.1 Weekly Monitor (`monitor_weekly.yml`)

```yaml
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
      - run: pip install -e .
      - run: devrel monitor report
      - run: devrel tracker sync
```

### 7.2 Release Trigger (`on_release.yml`)

```yaml
on:
  release:
    types: [published]

jobs:
  devrel:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e .
      - run: |
          RELEASE_URL="${{ github.event.release.html_url }}"
          devrel content social --tone ibm --platform both --context "$RELEASE_URL"
          devrel content social --tone personal --platform both --context "$RELEASE_URL"
          devrel content technical-blog --context "$RELEASE_URL"
          devrel content blog-outline --context "$RELEASE_URL"
          devrel docs update --context "$RELEASE_URL"
```

### 7.3 Manual Dispatch (`manual_dispatch.yml`)

```yaml
on:
  workflow_dispatch:
    inputs:
      workstream:
        description: 'Workstream to run'
        required: true
        type: choice
        options: [content, monitor, demo, tracker, docs]
      sub_agent:
        description: 'Sub-agent (e.g., social, technical-blog, report)'
        required: true
        type: string
      context:
        description: 'Context input (URL, text, etc.)'
        required: false
        type: string
      flags:
        description: 'Additional flags (e.g., --tone personal --platform twitter)'
        required: false
        type: string

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e .
      - run: devrel ${{ inputs.workstream }} ${{ inputs.sub_agent }} ${{ inputs.flags }} --context "${{ inputs.context }}"
```

---

## 8. Stack

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Matches Mellea, team familiarity |
| CLI framework | Typer | Type-safe CLI from type hints, less boilerplate than Click |
| GitHub API | PyGithub | Mature, well-documented, covers all needed operations |
| LLM reliability | Mellea | Structured output, requirements, rejection sampling |
| Templates | Jinja2 | Standard, separates prompts from logic |
| Testing | pytest | Required for demo validation, used throughout |
| Config | PyYAML + pydantic-settings | YAML files with env var overrides |
| Web scraping | httpx + beautifulsoup4 | For Context Resolver web URL fetching |
| GitHub Actions | Native | Scheduled + event-driven + manual triggers |

---

## 9. Build Order

Based on agreed priority. Each phase builds on the previous one.

### Phase 1: Foundation + Content Agent
- Build core layer: Context Resolver, Skill Loader, GitHub Client, LLM Client, Config
- Write initial skill files: `social-post.md`, `mellea-knowledge.md`, `tone-personal.md`, `tone-ibm.md`, `twitter-conventions.md`, `linkedin-conventions.md`, `de-llmify.md`
- Build Social Post Agent with skill manifest (both tones, both platforms)
- Build Technical Blog Agent with skill manifest
- Set up CLI entry point (`devrel`) and project structure
- Deliverable: `devrel content social` and `devrel content technical-blog` working end-to-end with skills loaded conditionally

### Phase 2: Monitor Agent + Intelligence Feed
- Build Monitor agent: metrics collection, mention tracking, report generation
- Write skill files: `weekly-report.md`, `sentiment-scoring.md`, `mention-evaluation.md`
- Add sentiment classification via Mellea `@generative`
- Implement briefs directory: monitor writes structured JSON after each run
- Build Content Suggest agent (`devrel content suggest`) that reads briefs
- Update Context Resolver to handle `brief:` prefix
- Set up weekly GitHub Action
- Deliverable: `devrel monitor report` running weekly, `devrel content suggest` producing content ideas from monitor data

### Phase 3: Demo Pipeline
- Build Pipeline core component (`core/pipeline.py`) with retry logic
- Build Ideation agent (standalone, produces concept files)
- Build Code Gen agent with `--repair-context` support for retries
- Build Test Runner (pytest harness, produces structured `TestResult`)
- Build Packager agent
- Write skill files: `ideation.md`, `code-generation.md`, `packaging.md`
- Wire pipeline: `devrel demo run` chains generate -> test -> package with retry on test failure
- Deliverable: `devrel demo ideate` standalone, `devrel demo run --concept X` automated pipeline

### Phase 4: Asset Tracker
- Build Log Asset agent with GitHub Project board integration
- Build Sync agent
- Build post-hook system (`core/hooks.py`)
- Wire post-hook: demo packager -> tracker (auto-log completed demos)
- Write skill files: `asset-extraction.md`, `issue-formatting.md`
- Deliverable: `devrel tracker log` (user-initiated for published content), `devrel tracker sync`, auto-logging for demos

### Phase 5: Docs Agents
- Build Writer agent (PR-based doc updates)
- Build Reviewer agent (LLM-readability evaluation)
- Write skill files: `writing-standards.md`, `llm-readability.md`, `review-criteria.md`
- Set up release-triggered GitHub Action
- Deliverable: `devrel docs update` and `devrel docs review`

---

## 10. Automation Coverage Estimate

| Task | Current (manual) | After Phase 5 | How |
|---|---|---|---|
| Social post drafting | 100% manual | 80% automated | Agent generates, human reviews and posts |
| Blog writing | 100% manual | 50% automated | Agent drafts, human edits and publishes |
| Blog outlines | 100% manual | 90% automated | Agent generates skeleton, human fills in |
| Content ideation | 100% manual | 70% automated | Monitor briefs feed content suggest agent |
| Asset tracking | 100% manual | 75% automated | User-initiated for published content, auto for demos |
| Metrics collection | 80% manual | 95% automated | Agent collects and reports |
| Sentiment monitoring | 100% manual | 85% automated | Agent scans and classifies |
| Demo creation | 100% manual | 50% automated | Human approves concept, pipeline automates the rest |
| Doc updates | 100% manual | 60% automated | Agent drafts PRs, human reviews |
| Doc review | 100% manual | 70% automated | Agent flags issues, human prioritizes |

**Estimated overall automation: 35-45%** of DevRel workload, with the highest gains in content drafting, metrics collection, and the demo execution pipeline (generate/test/package runs unattended after concept approval).

---

## 11. Resolved Design Decisions

These were originally open questions, now resolved:

1. **Rate limiting (RESOLVED):** Exponential backoff with configurable retry counts. The GitHub Client and LLM Client in core will both implement a shared `RetryPolicy` with defaults of 3 retries, 1s/2s/4s backoff. Configurable per-agent in `config.yml` if needed.
2. **Output storage (RESOLVED):** Generated drafts save to a `drafts/` directory in the repo, gitignored, with timestamped filenames (e.g., `drafts/social-post-2026-04-05-143022.md`). Agents also print a summary to stdout. The `--stdout-only` flag skips file writing for scripting use cases.
3. **Multi-model routing (RESOLVED):** Single model to start (configured in `config.yml`). Per-agent overrides available via the `llm.overrides` config key but not used until there's a proven need. Lighter models for classification tasks (sentiment scoring) can be added in Phase 2+.
4. **Mention data sources (RESOLVED):** Social platforms have varying levels of API access. The monitor agent will use a pluggable `MentionSource` interface so each platform can be swapped independently. Free/open sources (Reddit API, HN Firebase API, GitHub API, Stack Overflow API, PyPI stats) will be built in Phase 2 with native implementations. Twitter/X and LinkedIn mentions will use a third-party social listening service (vendor to be selected during Phase 2 implementation -- candidates include Mention.com, Data365, Keyhole, or similar). The `MentionSource` interface is:
    ```python
    class MentionSource:
        def fetch_mentions(self, keyword: str, since: datetime) -> list[Mention]
    ```
    This keeps the vendor decision non-blocking while ensuring the architecture supports it cleanly.
5. **Context Resolver caching (RESOLVED):** Simple file-based cache in `.cache/` directory (gitignored) with a 1-hour TTL for GitHub API responses. Cache key is the input URL or file path hash. The `--no-cache` flag bypasses the cache for fresh fetches.

---

## 12. Phase 1 Implementation Status

**Completed:** 2026-04-06

Phase 1 (Foundation + Content Agent) has been fully implemented. All milestones (1.1-1.5) are complete. Below is a summary of what was built and any deviations from the original design.

### 12.1 What Was Built

| Component | Status | Files |
|---|---|---|
| Project scaffold | Complete | pyproject.toml, .gitignore, .env.example, all __init__.py |
| Config system | Complete | core/config.py, config.yml |
| Shared models | Complete | core/models.py (ContextSource, ContextBlock, DraftOutput, RetryPolicy) |
| Context Resolver | Complete | core/context_resolver.py (PR, issue, release, web, file, text inputs + caching) |
| Skill Loader | Complete | core/skill_loader.py (manifest resolution, conditional loading, frontmatter stripping) |
| GitHub Client | Complete | core/github_client.py (read/write ops, retry with backoff) |
| LLM Client | Complete | core/llm_client.py (ollama + openai backends, Jinja2 templates, Mellea structured output) |
| Draft output utility | Complete | core/output.py |
| Skill files (8) | Complete | skills/content/ (5 files) + skills/shared/ (3 files) |
| Templates (2) | Complete | templates/content/social_post.j2, technical_blog.j2 |
| CLI entry point | Complete | cli/main.py, cli/commands/content.py |
| Social Post Agent | Complete | agents/content/social_post.py |
| Technical Blog Agent | Complete | agents/content/technical_blog.py |
| Unit tests | Complete | tests/test_config.py, test_context_resolver.py, test_skill_loader.py |
| Integration tests | Complete | tests/test_agents/test_social_post.py (8 tests), test_technical_blog.py (6 tests) |

### 12.2 Implementation Notes and Deviations

1. **Build system:** Uses hatchling (not setuptools). Skills and templates directories are included in the wheel via `force-include` in `pyproject.toml` (added in Phase 2).

2. **ContextBlock.combined_text:** Implemented as a `model_validator` that auto-assembles from sources, rather than a manually computed field. This is cleaner than the original spec.

3. **LLM Client backends:** Two backends implemented: `_OllamaBackend` (httpx to localhost:11434) and `_OpenAIBackend` (openai SDK). The `generate_structured` method includes a fallback path that extracts JSON from code fences when Mellea is unavailable.

4. **`generate_structured` not yet exercised:** Both content agents use `generate_with_template` (unstructured text). Structured output with Mellea validation will be more relevant for Phase 2 (sentiment classification) and Phase 3 (code validation).

5. **`add_to_project_board` is a stub:** Returns `NotImplementedError("Phase 4")`. Will be implemented when the Asset Tracker workstream is built.

6. **Test gaps:** No dedicated test files for `github_client.py`, `llm_client.py`, or `output.py`. The `tests/fixtures/sample_pr.py` fixture exists but is not imported by any test. These should be addressed in Phase 2 or as tech debt.

7. **CI not yet configured:** `.github/workflows/` directory exists but is empty. A CI workflow should be added early in Phase 2.

8. **Async infrastructure pre-provisioned:** `pytest-asyncio` is installed and `asyncio_mode=auto` is configured, but no async code exists yet. This will be useful for Phase 2 mention fetching.

### 12.3 Phase 1 Exit Criteria Verification

- [x] `devrel content social --context "..." --tone personal --platform twitter` produces a valid draft
- [x] `devrel content social --tone ibm --platform both --context "..."` produces two drafts
- [x] `devrel content technical-blog --context "..."` produces a markdown blog post
- [x] All unit tests pass (test_config: 4, test_context_resolver: 8, test_skill_loader: 9)
- [x] All integration tests pass with mocked LLM (test_social_post: 8, test_technical_blog: 6)
- [x] Skill files are complete and load correctly (8 skills across content/ and shared/)

---

## 13. Phase 2 Implementation Status

**Completed:** 2026-04-06

Phase 2 (Monitor Agent + Intelligence Feed) has been fully implemented. All planned capabilities are operational: mention tracking across 4 platforms, weekly report generation with sentiment classification, a briefs system for inter-agent data sharing, and a Content Suggest agent that bridges the monitor and content workstreams.

### 13.1 What Was Built

| Component | Status | Files |
|---|---|---|
| Mention models | Complete | core/models.py (Mention, SentimentResult, ContentSuggestion) |
| MentionSource ABC | Complete | core/mention_sources/__init__.py |
| Reddit source | Complete | core/mention_sources/reddit.py (3 subreddits, dedup, 2s rate limit) |
| Hacker News source | Complete | core/mention_sources/hackernews.py (Algolia API, stories + comments) |
| GitHub Discussions source | Complete | core/mention_sources/github_discussions.py (GraphQL API, token-gated) |
| PyPI source | Complete | core/mention_sources/pypi.py (JSON + pypistats APIs) |
| Source registry | Complete | core/mention_sources/registry.py (explicit dict, get_source/get_all/get_available) |
| Briefs system | Complete | core/briefs.py (save_brief, load_brief, get_brief_date) |
| Context Resolver brief: prefix | Complete | core/context_resolver.py (added _resolve_brief) |
| Config (monitor fields) | Complete | core/config.py, config.yml (monitor section) |
| Monitor Report agent | Complete | agents/monitor/report.py (stats + mentions + sentiment + template + brief) |
| Monitor Mentions agent | Complete | agents/monitor/mentions.py (fetch + filter + sentiment + brief) |
| Content Suggest agent | Complete | agents/content/suggest.py (auto-reads briefs + GitHub activity) |
| Monitor skills (3) | Complete | skills/monitor/weekly-report.md, sentiment-scoring.md, mention-evaluation.md |
| Content suggest skill | Complete | skills/content/suggest.md |
| Templates (2) | Complete | templates/monitor/weekly_report.j2, templates/content/suggest.j2 |
| CLI monitor commands | Complete | cli/commands/monitor.py (report, mentions) |
| CLI suggest command | Complete | cli/commands/content.py (suggest added) |
| CI workflow | Complete | .github/workflows/ci.yml (Python 3.11+3.12, ruff + pytest) |
| Weekly monitor action | Complete | .github/workflows/monitor_weekly.yml (Mon 9am UTC + dispatch) |
| Tech debt tests | Complete | test_github_client.py (7), test_llm_client.py (6), test_output.py (4) |
| Mention source tests | Complete | test_reddit.py (3), test_hackernews.py (2), test_pypi.py (2), test_registry.py (4) |
| Briefs tests | Complete | test_briefs.py (5, incl. context resolver brief: prefix) |
| Agent tests | Complete | test_monitor_report.py (4), test_monitor_mentions.py (4), test_content_suggest.py (4) |

**Total new tests:** 45 (bringing grand total to 80)

### 13.2 Implementation Notes and Deviations

1. **`MentionBatch` and `MonitorReport` models defined but unused:** These were added to `core/models.py` as designed but are not consumed by any agent. The agents work with raw `list[Mention]` and string outputs respectively. These models may become useful in Phase 4 (Asset Tracker) or can be removed as dead code.

2. **`_classify_sentiment` duplicated:** Both `agents/monitor/report.py` and `agents/monitor/mentions.py` contain an identical `_classify_sentiment` helper. This should be extracted to `agents/monitor/__init__.py` if duplication becomes a maintenance burden.

3. **`get_available_sources()` added beyond plan:** The registry module includes a `get_available_sources()` function that filters by `is_available()`. This was not in the original plan but is a natural extension that the CLI uses.

4. **Missing test file:** `tests/test_mention_sources/test_github_discussions.py` was planned but not created. GitHub Discussions source is implemented but untested.

5. **`generate_structured` now exercised:** Phase 2 delivers the first real use of `LLMClient.generate_structured` via `SentimentResult(Literal["positive","negative","neutral","mixed"])`. Both monitor agents use it for mention sentiment classification.

6. **Mention sources use httpx consistently:** All 4 platform implementations use httpx for HTTP requests, consistent with the existing Context Resolver pattern. No new HTTP dependencies were added.

7. **Reddit ternary precedence bug found and fixed:** The initial Reddit source had a Python operator precedence bug in the timestamp comparison (`created < since.replace(...) if ... else since`). This was caught during testing and fixed by extracting the timezone-aware comparison to a separate variable.

8. **pyproject.toml force-include:** Added `[tool.hatch.build.targets.wheel.force-include]` for `skills/` and `templates/` directories to ensure they are included in wheel builds.

### 13.3 Phase 2 Exit Criteria Verification

- [x] `devrel monitor report --help` shows all flags (--source, --stdout-only, --no-cache)
- [x] `devrel monitor mentions --help` shows all flags (--source, --stdout-only)
- [x] `devrel content suggest --help` shows suggest command with --context, --stdout-only/--save, --no-cache
- [x] Sentiment classification uses `generate_structured` with `SentimentResult`
- [x] Briefs system saves/loads JSON files via `brief:` prefix in Context Resolver
- [x] All 80 unit tests pass (`pytest tests/ -v -m "not integration"`)
- [x] `ruff check .` passes with no errors
- [x] CI workflow runs on push/PR with Python 3.11+3.12 matrix
- [x] Weekly monitor GitHub Action configured for Monday 9am UTC

---

## 14. Phase 3 Implementation Status

**Completed:** 2026-04-07

Phase 3 (Demo Pipeline) has been fully implemented. The pipeline engine, all four demo agents, skill files, templates, CLI commands, and tests are operational. The `devrel demo run` command chains generate → test → package with automatic retry on test failure.

### 14.1 What Was Built

| Component | Status | Files |
|---|---|---|
| Pipeline core | Complete | core/pipeline.py (Pipeline class, StageResult dataclass, retry logic) |
| Demo models | Complete | core/models.py (TestResult dataclass, DemoConcept model) |
| Demo config | Complete | core/config.py (demo_output_dir, demo_retry_budget, demo_test_timeout) |
| Concept parser | Complete | agents/demo/__init__.py (parse_concept_file with :N selector) |
| Ideation agent | Complete | agents/demo/ideation.py (concept generation with brief loading) |
| Code Gen agent | Complete | agents/demo/code_gen.py (file extraction, repair context support) |
| Test Runner | Complete | agents/demo/test_runner.py (pytest harness, smoke test fallback) |
| Packager agent | Complete | agents/demo/packager.py (README generation, code polish) |
| Pipeline wiring | Complete | agents/demo/pipeline.py (generate → test → package with retry) |
| CLI commands (5) | Complete | cli/commands/demo.py (ideate, run, generate, test, package) |
| Demo skills (3) | Complete | skills/demo/ideation.md, code-generation.md, packaging.md |
| Demo templates (3) | Complete | templates/demo/concept.j2, code_gen.j2, readme.j2 |
| Pipeline tests | Complete | tests/test_pipeline.py (7 tests) |
| Concept parser tests | Complete | tests/test_agents/test_demo_init.py (5 tests) |
| Ideation tests | Complete | tests/test_agents/test_demo_ideation.py (4 tests) |
| Code gen tests | Complete | tests/test_agents/test_demo_code_gen.py (5 tests) |
| Test runner tests | Complete | tests/test_agents/test_demo_test_runner.py (6 tests) |
| Packager tests | Complete | tests/test_agents/test_demo_packager.py (5 tests) |
| Pipeline integration tests | Complete | tests/test_agents/test_demo_pipeline.py (5 tests) |

**Phase 2 tech debt resolved:**

| Item | Status | Details |
|---|---|---|
| GitHub Discussions test | Complete | tests/test_mention_sources/test_github_discussions.py (4 tests) |
| classify_sentiment extraction | Complete | agents/monitor/__init__.py (shared helper, report.py + mentions.py updated) |
| Unused models removed | Complete | MentionBatch and MonitorReport removed from core/models.py |
| demos/ in .gitignore | Complete | .gitignore updated |

**Total new tests:** 41 (bringing grand total to 121 passing, 1 skipped)

### 14.2 Implementation Notes and Deviations

1. **CLI uses `typer.Argument` for concept/path:** The plan specified `typer.Option("--concept")` but Python 3.9 + Typer's `get_type_hints()` doesn't support `str | None` syntax at runtime. Changed to positional arguments: `devrel demo run "concept text"` and `devrel demo test ./demos/my_demo`. This is cleaner CLI UX than requiring `--concept`.

2. **File extraction uses regex:** `code_gen.py` extracts files from LLM output using a regex matching ````filename\n...```` code blocks. This is simpler than the plan's suggested approach and handles all expected output formats.

3. **Smoke test for demos without test files:** `test_runner.py` falls back to importing the main module as a smoke test when no `test_*.py` files exist in the demo directory. This wasn't explicitly in the plan but is a natural safety net.

4. **`__test__ = False` on TestResult:** Added to prevent pytest from trying to collect the `TestResult` dataclass as a test class.

5. **Pipeline retry feeds `repair_context`/`attempt` as kwargs:** The code gen agent's `run()` signature accepts `repair_context` and `attempt` as optional kwargs plus `**kwargs` for pipeline compatibility. This matches the pipeline's retry mechanism cleanly.

6. **Phase 2 status doc note:** Section 13.1 originally referenced `MentionBatch` and `MonitorReport` in the "What Was Built" table. These were removed during Phase 3 tech debt cleanup, and Section 13.1 was corrected in Phase 7.

### 14.3 Phase 3 Exit Criteria Verification

- [x] `devrel demo ideate --help` shows all flags (--context, --stdout-only)
- [x] `devrel demo run --help` shows concept argument and flags (--context, --output-dir)
- [x] `devrel demo generate "concept"` produces files in demos/ directory
- [x] `devrel demo test ./path` runs pytest and returns structured result
- [x] `devrel demo package ./path` produces README.md
- [x] `devrel demo run "concept"` chains all 3 stages automatically
- [x] Test failure triggers automatic retry with error context fed back to code gen
- [x] Retry budget exhaustion stops pipeline and reports failures
- [x] All 121 tests pass (`pytest tests/ -q`)
- [x] `ruff check .` passes with no errors

---

## 15. Phase 4 Implementation Status

**Completed:** 2026-04-07

Phase 4 (Asset Tracker) has been fully implemented. The log asset agent, sync agent, post-hook system, GitHub Projects v2 GraphQL integration, CLI commands, skills, templates, and tests are all operational.

### 15.1 What Was Built

| Component | Status | Files |
|---|---|---|
| Asset models | Complete | core/models.py (AssetMetadata, AssetExtractionResult) |
| Tracker config | Complete | core/config.py (tracker_project_board_id, tracker_label_prefix, tracker_scan_platforms), config.yml |
| Platform detection | Complete | agents/tracker/__init__.py (detect_platform, infer_asset_type, regex-based URL rules) |
| Log Asset agent | Complete | agents/tracker/log_asset.py (LLM extraction + explicit overrides + issue creation + project board) |
| Sync agent | Complete | agents/tracker/sync.py (scan briefs + drafts, cross-reference tracked issues, gap report) |
| Post-hook engine | Complete | core/hooks.py (static dict registry, pattern matching, lazy imports, best-effort execution) |
| Packager hook wiring | Complete | agents/demo/packager.py (no_hooks kwarg, fires run_post_hooks on success) |
| GitHub Projects v2 GraphQL | Complete | core/github_client.py (addProjectV2ItemById, updateProjectV2ItemFieldValue, field ID lookup) |
| Tracker skills (2) | Complete | skills/tracker/asset-extraction.md, issue-formatting.md |
| Tracker template | Complete | templates/tracker/issue_body.j2 |
| CLI tracker commands | Complete | cli/commands/tracker.py (log, sync), cli/main.py (tracker typer registered) |
| CLI --no-hooks flag | Complete | cli/commands/demo.py (package command) |
| Platform detection tests | Complete | tests/test_agents/test_tracker_init.py (12 tests) |
| Log Asset agent tests | Complete | tests/test_agents/test_tracker_log_asset.py (5 tests) |
| Sync agent tests | Complete | tests/test_agents/test_tracker_sync.py (4 tests) |
| Post-hook tests | Complete | tests/test_hooks.py (11 tests) |
| Project board tests | Complete | tests/test_github_client.py (3 new tests added) |

**Total new tests:** 35 (bringing grand total to 156 passing, 1 skipped)

### 15.2 Implementation Notes and Deviations

1. **`--no-hooks` on `package` only, not `run`:** The plan mentioned adding `--no-hooks` to both the `package` and `run` pipeline commands. In practice, only the `package` CLI command received the flag. The pipeline (`devrel demo run`) passes through kwargs to the packager, so `no_hooks` can be set programmatically but is not exposed as a `run` command flag. This is sufficient because hooks fire from the packager stage regardless of entry point.

2. **Hooks check `kwargs.get("no_hooks")`, not `stdout_only`:** The plan suggested checking `stdout_only` to skip hooks. The implementation uses a dedicated `no_hooks` kwarg instead, which is cleaner separation of concerns — `stdout_only` controls output formatting, `no_hooks` controls side effects.

3. **`sync` CLI uses `--source/-s`, not `--platform/-p`:** The plan specified `--platform/-p` for the sync command's filter option. The implementation uses `--source/-s` to be consistent with the monitor CLI commands which also use `--source`.

4. **Platform detection via regex, not `urlparse`:** `agents/tracker/__init__.py` initially imported `urlparse` but the implementation uses regex-only matching via `_PLATFORM_RULES`. The unused `urlparse` import was removed during ruff cleanup.

5. **`add_to_project_board` was not a stub:** The plan described implementing it as tech debt from Phase 3. In fact, it was implemented fresh in Phase 4 — there was no pre-existing stub, just a missing method. The implementation uses httpx for GraphQL calls, consistent with the rest of the codebase.

6. **12 platform detection tests:** The plan specified ~7 test cases for platform detection. The implementation has 12 tests covering all 7 platform rules plus both `detect_platform` and `infer_asset_type` functions with positive and negative cases.

7. **`generate_structured` with `AssetExtractionResult`:** This is the second real use of `LLMClient.generate_structured` (after Phase 2's `SentimentResult`). The log asset agent uses it to extract asset metadata from context when explicit overrides are not provided.

### 15.3 Phase 4 Exit Criteria Verification

- [x] `devrel tracker log --context "https://twitter.com/..." --help` shows all flags
- [x] `devrel tracker log --context "URL" --dry-run` prints issue body without creating
- [x] `devrel tracker log --type blog --title "Post" --link "URL"` uses explicit values
- [x] `devrel tracker sync --help` shows source filter flags
- [x] `devrel tracker sync` reports untracked assets from briefs/drafts
- [x] Demo packager fires post-hook (unless `--no-hooks`)
- [x] `add_to_project_board` creates project items via GraphQL
- [x] All 156 tests pass (`pytest tests/ -q`)
- [x] `ruff check .` passes with no errors

---

## 16. Phase 5 Implementation Status

Phase 5 implemented the **Docs Agents** workstream: a writer agent that creates documentation PRs and a reviewer agent that audits existing docs.

### 16.1 What Was Built

| Component | Status | Details |
|-----------|--------|---------|
| `agents/docs/__init__.py` | Complete | Package init |
| `agents/docs/writer.py` | Complete | Resolves context, generates doc update plan via `generate_structured(DocUpdatePlan)`, fetches existing file content, generates updates with file block markers, creates branch + commit + PR via GitHub API |
| `agents/docs/reviewer.py` | Complete | Discovers docs via `get_tree`, fetches content, renders template manually, calls `generate_structured(DocReviewReport)` with text fallback, groups findings by severity, optionally creates GitHub issues for critical findings |
| `skills/docs/writing-standards.md` | Complete | Documentation writing style guide |
| `skills/docs/llm-readability.md` | Complete | LLM-friendly documentation standards |
| `skills/docs/review-criteria.md` | Complete | Review criteria with severity levels and finding categories |
| `templates/docs/update.j2` | Complete | Doc update prompt with file block output format |
| `templates/docs/review_checklist.j2` | Complete | Review prompt requesting JSON findings array |
| `cli/commands/docs.py` | Complete | `update` and `review` commands with all flags |
| `cli/main.py` (modification) | Complete | Added docs workstream typer group |
| `core/github_client.py` (modification) | Complete | Added `get_tree()` and `get_file_content()` methods |
| `core/models.py` (modification) | Complete | Added `DocFinding`, `DocReviewReport`, `DocUpdatePlan` models |
| `core/config.py` (modification) | Complete | Added `docs_target_dir`, `docs_branch_prefix`, `docs_max_files_per_pr` |
| `.github/workflows/on_release.yml` | Complete | Release-triggered: content generation + docs update + docs review |
| `.github/workflows/manual_dispatch.yml` | Complete | Manual dispatch for any workstream |
| `tests/test_agents/test_docs_writer.py` | Complete | 6 tests |
| `tests/test_agents/test_docs_reviewer.py` | Complete | 6 tests |
| `tests/test_github_client.py` (3 new) | Complete | get_tree, get_file_content, create_pr |

**Total new tests:** 15 (bringing grand total to 171 passing)

### 16.2 Implementation Notes and Deviations

1. **Writer uses GitHub API, not local git:** The writer agent creates branches and commits entirely through the GitHub API (`repo.create_git_ref`, `repo.create_file`, `repo.update_file`). This means it works without a local checkout and is suitable for CI environments.

2. **Reviewer renders templates manually:** Because the reviewer needs to pass a rendered prompt to `generate_structured` (not `generate_with_template`), it accesses `llm._jinja.get_template().render()` directly. This is a pragmatic choice — the alternative would be adding a `render_template` method to LLMClient.

3. **File block extraction uses regex:** The writer parses LLM output for ````file:path```` markers using `r"```file:(\S+)\n(.*?)```"`. This is simple and works well with the template instructions that specify this format.

4. **DocUpdatePlan for scoping:** Before generating content, the writer asks the LLM to produce a `DocUpdatePlan` (structured output) identifying which files to create or update. This prevents the LLM from generating content for unrelated files.

### 16.3 Phase 5 Exit Criteria Verification

- [x] `devrel docs update --help` shows all flags
- [x] `devrel docs review --help` shows all flags
- [x] Writer creates branch + PR via GitHub API
- [x] Reviewer discovers and reviews docs files
- [x] Reviewer creates GitHub issues for critical findings
- [x] All 171 tests pass (`pytest tests/ -q`)
- [x] `ruff check .` passes with no errors

---

## 17. Phase 6 Implementation Status

Phase 6 completed the remaining agents from the design doc: **Blog Outline**, **Personal Blog**, and **Publications Tracker**.

### 17.1 What Was Built

| Component | Status | Details |
|-----------|--------|---------|
| `agents/content/blog_outline.py` | Complete | Simplest content agent — no conditional skills, no post-processing. Generates IBM Research blog skeleton (headers + bullets). |
| `agents/content/personal_blog.py` | Complete | Same pattern as `technical_blog.py` — includes de-llmify post-processing. Conversational first-person tone. |
| `agents/monitor/publications.py` | Complete | Fetches tracked assets from GitHub issues (label: asset-tracking), loads mention briefs, cross-references, generates LLM report, saves brief. |
| `skills/content/blog-outline.md` | Complete | IBM Research skeleton format: "What It Is", "Why It Matters", "How To Use It" |
| `skills/content/personal-blog.md` | Complete | Conversational tone guide, personal opinions OK, 600-1200 words |
| `skills/monitor/publications-tracking.md` | Complete | Publication performance evaluation from available data |
| `templates/content/blog_outline.j2` | Complete | Outline-only task prompt |
| `templates/content/personal_blog.j2` | Complete | Conversational blog post task prompt |
| `templates/monitor/publications_report.j2` | Complete | Report with tracked assets, mention data, statistics |
| `cli/commands/content.py` (modification) | Complete | Added `blog-outline` and `personal-blog` commands |
| `cli/commands/monitor.py` (modification) | Complete | Added `publications` command |
| `tests/test_agents/test_blog_outline.py` | Complete | 5 tests |
| `tests/test_agents/test_personal_blog.py` | Complete | 4 tests |
| `tests/test_agents/test_monitor_publications.py` | Complete | 5 tests |

**Total new tests:** 14 (bringing grand total to 186 passing)

### 17.2 Implementation Notes and Deviations

1. **Publications Tracker aggregates existing data:** No analytics APIs were added. The tracker fetches tracked GitHub issues (label: `asset-tracking`) and loads existing monitor briefs, then cross-references them via LLM to produce a performance report. This is consistent with the "GitHub is the message bus" design principle.

2. **Blog Outline has no post-processing:** Unlike Technical Blog and Personal Blog, the Blog Outline agent has an empty `post_processing` list. Outlines are bullets, not prose, so de-llmify is not applicable.

3. **Publications uses `sentiment-scoring` skill:** The publications tracker reuses the existing `monitor/sentiment-scoring` skill alongside the new `monitor/publications-tracking` skill, enabling sentiment-aware performance analysis.

### 17.3 Phase 6 Exit Criteria Verification

- [x] `devrel content blog-outline --help` shows flags
- [x] `devrel content personal-blog --help` shows flags
- [x] `devrel monitor publications --help` shows flags
- [x] No `(planned)` markers remain in design doc Section 3.1
- [x] Design doc has Sections 16 and 17
- [x] All 186 tests pass (`pytest tests/ -q`)
- [x] `ruff check .` passes with no errors

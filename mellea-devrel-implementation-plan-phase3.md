# Mellea DevRel Agent System - Phase 3 Implementation Plan

**Date:** 2026-04-06
**Design Spec:** mellea-devrel-agents-design.md (updated 2026-04-06, Phase 2 Complete)
**Prerequisite:** Phase 2 complete (Monitor Agent + Intelligence Feed)
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

## Phase 3: Demo Pipeline

**Goal:** `devrel demo ideate` produces demo concepts standalone.
`devrel demo run --concept X` chains generate → test → package with automatic
retry on test failure (up to 2 retries). Individual stages (`devrel demo generate`,
`devrel demo test`, `devrel demo package`) are also callable independently.

**Estimated scope:** ~18 new files, ~2,000 lines of code + ~600 lines of
skill/template content.

---

### Milestone 3.0: Phase 2 Tech Debt

Address gaps from Phase 2 before building new features.

#### Task 3.0.1 [test] Add missing GitHub Discussions source test

The `core/mention_sources/github_discussions.py` implementation exists but has
no test coverage. Add a dedicated test file.

**File:** `tests/test_mention_sources/test_github_discussions.py`

**Test cases:**
- `fetch_mentions` parses GraphQL response into `Mention` objects (mock httpx)
- `is_available` returns `False` when `DEVREL_GITHUB_TOKEN` is unset
- `is_available` returns `True` when token is present (mock env)
- Empty response returns empty list

**Pattern:** Follow `test_reddit.py` -- import module, `patch.object(mod, "httpx")`,
mock the GraphQL response JSON structure.

---

#### Task 3.0.2 [code] Extract shared `_classify_sentiment` helper

Both `agents/monitor/report.py` and `agents/monitor/mentions.py` contain an
identical `_classify_sentiment` function. Extract it to a shared location.

**File:** `agents/monitor/__init__.py`

**Changes:**
- Move `_classify_sentiment(llm: LLMClient, text: str) -> str` into
  `agents/monitor/__init__.py` as `classify_sentiment` (public, no underscore)
- Update `agents/monitor/report.py` to import from `agents.monitor`
- Update `agents/monitor/mentions.py` to import from `agents.monitor`
- Verify existing tests still pass (no test changes needed -- they mock LLMClient)

---

#### Task 3.0.3 [code] Remove unused models or add usage markers

`MentionBatch` and `MonitorReport` in `core/models.py` are defined but unused.

**Decision:** Remove both models. They add no value currently and can be re-added
if a concrete consumer emerges in Phase 4. Add a comment noting they were removed
and why:

```python
# MentionBatch and MonitorReport were removed in Phase 3 cleanup.
# Re-add when Phase 4 (Asset Tracker) needs structured batch/report models.
```

---

### Milestone 3.1: Pipeline Core + Models

Build the reusable pipeline engine and data models that all demo agents depend on.

#### Task 3.1.1 [code] Create Pipeline core component

**File:** `core/pipeline.py`

Implement the `Pipeline` class as specified in design doc Section 5.1.

**Classes:**

```python
@dataclass
class StageResult:
    stage_name: str
    success: bool
    output: dict          # Passed as input to the next stage
    error_context: str | None  # Fed back on retry

class Pipeline:
    def __init__(
        self,
        stages: list[tuple[str, Callable]],
        on_stage_failure: dict | None = None,
    ):
        ...

    def run(self, initial_input: dict) -> list[StageResult]:
        """Run all stages sequentially. Stop on unrecoverable failure."""
        ...

    def _handle_failure(self, stage_name, stage_fn, result,
                        previous_input, config) -> StageResult:
        """Retry the previous stage with failure context."""
        ...

    def _get_previous_stage(self, stage_name) -> tuple[str, Callable]:
        """Look up the stage before the named one."""
        ...
```

**Behavior:**
- `run()` iterates stages, passing each stage's `output` dict as `**kwargs` to the next
- On failure: checks `on_stage_failure` dict for a retry config
- `retry_previous` action: re-runs the previous stage with `repair_context` and
  `attempt` injected into kwargs, then re-runs the failing stage with new output
- Returns list of all `StageResult`s (including retries)
- Logs stage transitions to stderr via `logging.getLogger("pipeline")`
- If no failure config or retries exhausted, stops pipeline and returns partial results

**No external dependencies.** Pure Python, no LLM calls.

---

#### Task 3.1.2 [code] Add demo-related models

**File:** `core/models.py` (modify)

Add:

```python
@dataclass
class TestResult:
    passed: bool
    total_tests: int
    failed_tests: int
    error_output: str | None    # stderr + pytest output
    failing_test_names: list[str]

class DemoConcept(BaseModel):
    title: str
    description: str
    target_audience: str
    complexity: Literal["S", "M", "L"]
    mellea_features: list[str]
    why_this_works: str
```

`TestResult` is a dataclass (not Pydantic) because it comes from pytest, not LLM.
`DemoConcept` is a Pydantic model because it will be used with `generate_structured`.

---

#### Task 3.1.3 [code] Add demo config fields

**File:** `core/config.py` (modify)

Add to `Settings`:

```python
demo_output_dir: str = "demos"
demo_retry_budget: int = 2
demo_test_timeout: int = 120  # seconds
```

**File:** `config.yml` (modify)

Add:

```yaml
demo:
  output_dir: demos
  retry_budget: 2
  test_timeout: 120
```

---

#### Task 3.1.4 [test] Pipeline core tests

**File:** `tests/test_pipeline.py`

**Test cases:**
- Three-stage pipeline runs all stages and returns 3 StageResults
- Pipeline stops on failure when no retry config exists
- Pipeline retries previous stage on failure (mock stages, verify retry count)
- Retry injects `repair_context` and `attempt` into kwargs
- Retry budget exhaustion stops pipeline and returns partial results
- `_get_previous_stage` raises ValueError for first stage (no previous)
- Empty stages list returns empty results

**Pattern:** All stages are plain functions or lambdas returning `StageResult`.
No LLM mocking needed.

---

### Milestone 3.2: Demo Skills + Templates

Write the skill and template files that demo agents will use. These have no code
dependencies and can be built in parallel with Milestone 3.1.

#### Task 3.2.1 [skill] Ideation skill

**File:** `skills/demo/ideation.md`

**Frontmatter:**
```yaml
---
name: ideation
description: How to generate compelling demo concepts for Mellea
category: demo
---
```

**Content guidance:**
- Demo concepts should showcase Mellea's core value: structured output validation,
  requirements, rejection sampling, instruct-validate-repair
- Each concept must be self-contained and runnable as a single Python script
- Target audience should be specific (ML engineers, backend devs, data scientists)
- Complexity ratings: S = <50 lines, M = 50-150 lines, L = 150+ lines
- Concepts should use real-world scenarios (not toy examples)
- Prefer concepts that highlight a single Mellea feature clearly over kitchen-sink demos
- Each concept must include a "Why this works" that explains the pedagogical value

---

#### Task 3.2.2 [skill] Code generation skill

**File:** `skills/demo/code-generation.md`

**Frontmatter:**
```yaml
---
name: code-generation
description: Code quality standards for generated Mellea demos
category: demo
---
```

**Content guidance:**
- All generated code must use actual Mellea APIs (no hallucinated functions)
- Include all necessary imports at the top of the file
- Include inline comments explaining each step
- Requirements.txt must list exact versions
- Main script must be runnable with `python main.py`
- Test file (`test_demo.py`) must: import main module, call primary function with
  sample input, assert output type, check no exceptions raised
- On repair: read the error output carefully, identify the specific failure, make
  minimal targeted changes (don't rewrite everything)
- Code style: Black-compatible formatting, type hints on public functions

---

#### Task 3.2.3 [skill] Packaging skill

**File:** `skills/demo/packaging.md`

**Frontmatter:**
```yaml
---
name: packaging
description: README and polish standards for completed demos
category: demo
---
```

**Content guidance:**
- README.md structure: Overview, Prerequisites, Installation, Usage, Expected
  Output, How It Works (Mellea features explained), License
- Code cleanup: remove debug prints, ensure consistent formatting, add docstrings
  to main functions only
- Expected Output section must show actual output (captured from test run)
- Prerequisites: Python version, Mellea version, any external dependencies
- Do not add features or change behavior -- packaging is polish only

---

#### Task 3.2.4 [template] Demo concept template

**File:** `templates/demo/concept.j2`

**Structure:**
```
System: You are a developer relations engineer creating demo concepts for Mellea.

{{ skills }}

Context about the feature or topic:
{{ context }}

{% if briefs %}
Recent project intelligence:
{{ briefs }}
{% endif %}

Task: Generate 3-5 demo concepts. For each concept provide:
- Title
- Description (2-3 sentences)
- Target audience
- Complexity (S/M/L)
- Mellea features used
- Why this works (1 sentence)

Format each concept as a markdown section starting with ## Concept N: {title}
```

---

#### Task 3.2.5 [template] Demo code generation template

**File:** `templates/demo/code_gen.j2`

**Structure:**
```
System: You are a senior Python developer generating demo code for Mellea.

{{ skills }}

Concept to implement:
{{ concept }}

{% if context %}
Additional context:
{{ context }}
{% endif %}

{% if repair_context %}
IMPORTANT - Previous attempt failed. Fix the following issues:
Attempt: {{ attempt }}
Error output:
{{ repair_context }}

Make minimal targeted changes to fix the specific errors above.
{% endif %}

Task: Generate the following files:
1. main.py - The demo script
2. test_demo.py - Basic test file
3. requirements.txt - Dependencies with versions

Return each file as a markdown code block with the filename as the language tag.
```

---

#### Task 3.2.6 [template] Demo README template

**File:** `templates/demo/readme.j2`

**Structure:**
```
System: You are a developer relations engineer writing documentation for a Mellea demo.

{{ skills }}

Demo code:
{{ code_content }}

Test results:
{{ test_output }}

Concept description:
{{ concept }}

Task: Generate a polished README.md for this demo following the structure in your skills.
Also suggest any code cleanup changes (formatting, comments, docstrings).
```

---

### Milestone 3.3: Demo Agents

Build the four demo agents. Ideation is standalone; the other three are designed
to work both independently and as pipeline stages.

#### Task 3.3.1 [code] Concept parser utility

**File:** `agents/demo/__init__.py`

Implement a concept parser that extracts a specific concept from a multi-concept
markdown file using the `:N` suffix notation.

```python
def parse_concept_file(path_with_selector: str) -> str:
    """Parse a concept file path with optional :N selector.

    Examples:
        "drafts/concepts.md:2" -> returns text of Concept 2
        "drafts/concepts.md" -> returns full file content
        "Some free text" -> returns the text as-is (not a file)
    """
```

**Behavior:**
- If input contains `:` and the base path exists as a file, split on last `:`
- Read the file, split on `## Concept N` headers
- Return the content of the selected concept (header + body)
- If no selector, return full file content
- If input is not a valid file path, return it as raw text (treat as inline concept)

---

#### Task 3.3.2 [code] Ideation agent

**File:** `agents/demo/ideation.py`

**SKILL_MANIFEST:**
```python
SKILL_MANIFEST = {
    "always": [
        "demo/ideation",
        "shared/mellea-knowledge",
    ],
    "conditional": {},
    "post_processing": [],
}
```

**`run()` signature:**
```python
def run(
    context_inputs: list[str] | None = None,
    stdout_only: bool = False,
) -> DraftOutput:
```

**Behavior:**
1. Resolve context via `resolve_context(context_inputs)` if provided
2. Optionally load latest briefs (weekly-report, mentions) for project intelligence
3. Load skills via manifest
4. Call `llm.generate_with_template("demo/concept", {...})`
5. Save draft via `save_draft("demo-ideation", content, stdout_only=stdout_only)`
6. Return `DraftOutput`

**Agent name:** `"demo-ideation"`

---

#### Task 3.3.3 [code] Code generation agent

**File:** `agents/demo/code_gen.py`

**SKILL_MANIFEST:**
```python
SKILL_MANIFEST = {
    "always": [
        "demo/code-generation",
        "shared/mellea-knowledge",
    ],
    "conditional": {},
    "post_processing": [],
}
```

**`run()` signature:**
```python
def run(
    concept: str,
    context_inputs: list[str] | None = None,
    repair_context: str | None = None,
    attempt: int = 0,
    output_dir: str | None = None,
) -> StageResult:
```

**Behavior:**
1. Parse concept via `parse_concept_file(concept)` from `agents.demo`
2. Resolve additional context if provided
3. Load skills via manifest
4. Call `llm.generate_with_template("demo/code_gen", {...})` including
   `repair_context` and `attempt` if present
5. Parse response to extract file blocks (main.py, test_demo.py, requirements.txt)
6. Write files to `output_dir` (default: `demos/{concept_slug}/`)
7. Return `StageResult(stage_name="generate", success=True, output={"path": output_dir})`

**File extraction:** Parse markdown code blocks with filename tags:
````
```main.py
...
```
````
Use a regex to extract `(filename, content)` pairs.

**On repair:** When `repair_context` is provided, the template includes the error
output and attempt number. The LLM is instructed to make minimal targeted fixes.

---

#### Task 3.3.4 [code] Test runner

**File:** `agents/demo/test_runner.py`

This is NOT an LLM agent. It is a pytest harness.

**`run()` signature:**
```python
def run(path: str, timeout: int | None = None) -> StageResult:
```

**Behavior:**
1. Verify `path` exists and contains Python files
2. Check for `requirements.txt` -- if present, install deps into a temporary venv
   or the current environment (use `subprocess.run(["pip", "install", "-r", ...])`)
3. Check for test files (`test_*.py` or `*_test.py`) -- if none exist, run a
   smoke test: attempt to import the main module
4. Run `pytest {path} --tb=short -q` via `subprocess.run`, capture stdout+stderr
5. Parse pytest output to extract pass/fail counts and failing test names
6. Return `StageResult` with:
   - `success = (return_code == 0)`
   - `output = {"path": path, "test_result": TestResult(...)}`
   - `error_context = stderr + stdout if failed`

**Timeout:** Default from `config.demo_test_timeout`. Pass through to
`subprocess.run(timeout=...)`. On timeout, return failure with
`error_context = "Test execution timed out after {n} seconds"`.

**No LLM calls, no skills, no templates.**

---

#### Task 3.3.5 [code] Packager agent

**File:** `agents/demo/packager.py`

**SKILL_MANIFEST:**
```python
SKILL_MANIFEST = {
    "always": [
        "demo/packaging",
        "shared/mellea-knowledge",
    ],
    "conditional": {},
    "post_processing": [],
}
```

**`run()` signature:**
```python
def run(
    path: str,
    concept: str | None = None,
    stdout_only: bool = False,
) -> StageResult:
```

**Behavior:**
1. Read all Python files from `path`
2. Read test output if available (look for `.test_result` file or accept from
   pipeline `output` dict)
3. Load skills via manifest
4. Call `llm.generate_with_template("demo/readme", {...})` with code content,
   test results, and concept description
5. Parse response to extract README.md content and any code cleanup suggestions
6. Write README.md to `path/README.md`
7. Apply code cleanup if suggested (optional -- just write the cleaned files)
8. Return `StageResult(stage_name="package", success=True, output={"path": path})`

**Warning on untested demos:** If no test results are available (manual run on
untested code), print a warning to stderr but proceed.

---

### Milestone 3.4: Pipeline Wiring + CLI

Wire the demo stages into a pipeline and add CLI commands.

#### Task 3.4.1 [code] Demo pipeline assembly

**File:** `agents/demo/pipeline.py`

```python
from core.pipeline import Pipeline
from agents.demo import code_gen, test_runner, packager

DEMO_PIPELINE = Pipeline(
    stages=[
        ("generate", code_gen.run),
        ("test", test_runner.run),
        ("package", packager.run),
    ],
    on_stage_failure={
        "test": {
            "action": "retry_previous",
            "retry_budget": 2,       # from config.demo_retry_budget
            "feed_output": True,
        },
    },
)

def run(concept: str, context_inputs: list[str] | None = None,
        output_dir: str | None = None) -> list[StageResult]:
    """Run the full demo pipeline: generate -> test -> package."""
    initial_input = {
        "concept": concept,
        "context_inputs": context_inputs,
        "output_dir": output_dir,
    }
    return DEMO_PIPELINE.run(initial_input)
```

**Note:** The pipeline's retry logic feeds `error_context` from the test stage
back to the generate stage as `repair_context`. The stage function signatures
must align: generate accepts `repair_context` and `attempt`; test returns
`error_context` on failure.

---

#### Task 3.4.2 [code] CLI demo commands

**File:** `cli/commands/demo.py`

**Commands:**

```python
import typer

app = typer.Typer(help="Demo pipeline commands")

@app.command()
def ideate(
    context: Annotated[list[str] | None, typer.Option("--context", "-c")] = None,
    stdout_only: Annotated[bool, typer.Option("--stdout-only")] = False,
):
    """Generate demo concepts from context."""

@app.command()
def run(
    concept: Annotated[str, typer.Option("--concept")] = ...,
    context: Annotated[list[str] | None, typer.Option("--context", "-c")] = None,
    output_dir: Annotated[str | None, typer.Option("--output-dir", "-o")] = None,
):
    """Run the full demo pipeline: generate -> test -> package."""

@app.command()
def generate(
    concept: Annotated[str, typer.Option("--concept")] = ...,
    context: Annotated[list[str] | None, typer.Option("--context", "-c")] = None,
    output_dir: Annotated[str | None, typer.Option("--output-dir", "-o")] = None,
):
    """Generate demo code from a concept (standalone, no pipeline)."""

@app.command()
def test(
    path: Annotated[str, typer.Option("--path", "-p")] = ...,
    timeout: Annotated[int | None, typer.Option("--timeout")] = None,
):
    """Run tests on a generated demo."""

@app.command()
def package(
    path: Annotated[str, typer.Option("--path", "-p")] = ...,
    concept: Annotated[str | None, typer.Option("--concept")] = None,
    stdout_only: Annotated[bool, typer.Option("--stdout-only")] = False,
):
    """Package a demo with README and polish."""
```

**File:** `cli/main.py` (modify)

Add:
```python
from cli.commands import demo
app.add_typer(demo.app, name="demo")
```

---

### Milestone 3.5: Tests

#### Task 3.5.1 [test] Concept parser tests

**File:** `tests/test_agents/test_demo_init.py`

**Test cases:**
- File with `:2` selector returns Concept 2 content
- File without selector returns full content
- Non-file input returns raw text
- Invalid selector (`:99` on 3-concept file) raises IndexError or ValueError
- File path with no colon returns full file (uses `tmp_path`)

---

#### Task 3.5.2 [test] Ideation agent tests

**File:** `tests/test_agents/test_demo_ideation.py`

**Test cases:**
- `run()` calls `generate_with_template` with `"demo/concept"` template
- Skill manifest loads ideation + mellea-knowledge
- Context is passed through to template variables
- Missing context (None) produces output without error
- Draft is saved via `save_draft` with agent name `"demo-ideation"`

**Pattern:** Triple-patch (LLMClient, resolve_context, save_draft). Same pattern
as test_social_post.py and test_content_suggest.py.

---

#### Task 3.5.3 [test] Code generation agent tests

**File:** `tests/test_agents/test_demo_code_gen.py`

**Test cases:**
- `run()` returns StageResult with success=True and output containing path
- Generated files are written to output_dir (use `tmp_path`)
- Repair context is passed to template when provided
- Attempt number is included in template variables on retry
- File extraction regex correctly parses markdown code blocks
- Missing concept file returns failure StageResult

**Pattern:** Patch LLMClient. Use `tmp_path` for output directory.

---

#### Task 3.5.4 [test] Test runner tests

**File:** `tests/test_agents/test_demo_test_runner.py`

**Test cases:**
- Passing tests return StageResult with success=True
- Failing tests return StageResult with success=False and error_context
- Missing path raises error or returns failure
- Timeout is enforced (mock subprocess.run to raise TimeoutExpired)
- Smoke test runs when no test files exist
- pytest output is parsed for pass/fail counts

**Pattern:** Mock `subprocess.run`. Create temporary demo directories with
`tmp_path`.

---

#### Task 3.5.5 [test] Packager agent tests

**File:** `tests/test_agents/test_demo_packager.py`

**Test cases:**
- `run()` reads code files from path and passes to template
- README.md is written to the demo directory
- Warning printed when no test results available
- Skill manifest loads packaging + mellea-knowledge
- StageResult contains success=True and path

**Pattern:** Patch LLMClient. Use `tmp_path` with sample Python files.

---

#### Task 3.5.6 [test] Pipeline integration tests

**File:** `tests/test_agents/test_demo_pipeline.py`

**Test cases:**
- Full pipeline runs 3 stages and returns 3 StageResults (mock all agents)
- Test failure triggers retry of generate stage (mock test_runner to fail once then pass)
- Retry passes repair_context to code_gen
- Retry budget exhaustion stops pipeline after N retries
- Pipeline handles generate failure (stops before test)

**Pattern:** Patch `code_gen.run`, `test_runner.run`, `packager.run`. Verify
call counts and kwargs.

---

### Milestone 3.6: Infrastructure

#### Task 3.6.1 [config] Add demos/ to .gitignore

**File:** `.gitignore` (modify)

Add:
```
demos/
```

Generated demos should not be committed by default.

---

## Summary

| Milestone | Tasks | New Files | Modified Files |
|---|---|---|---|
| 3.0 Tech Debt | 3 | 1 | 3 |
| 3.1 Pipeline + Models | 4 | 2 | 3 |
| 3.2 Skills + Templates | 6 | 6 | 0 |
| 3.3 Demo Agents | 5 | 5 | 0 |
| 3.4 Pipeline + CLI | 2 | 2 | 1 |
| 3.5 Tests | 6 | 6 | 0 |
| 3.6 Infrastructure | 1 | 0 | 1 |
| **Total** | **27** | **22** | **8** |

## Dependencies

```
Milestone 3.0 (tech debt)     -- no dependencies, do first
Milestone 3.1 (pipeline/models) -- no dependencies on 3.0
Milestone 3.2 (skills/templates) -- no dependencies on 3.1
   |
   +-- 3.1 + 3.2 must complete before 3.3
   |
Milestone 3.3 (agents)        -- depends on 3.1 (Pipeline, models) + 3.2 (skills, templates)
Milestone 3.4 (CLI/wiring)    -- depends on 3.3 (agents exist)
Milestone 3.5 (tests)         -- depends on 3.3 (agents exist) + 3.4 (pipeline wiring)
Milestone 3.6 (infra)         -- no dependencies, can be done anytime
```

**Parallelizable:** 3.0, 3.1, 3.2, and 3.6 can all be done in parallel.
3.3 and 3.4 are sequential after 3.1+3.2. 3.5 follows 3.4.

## Exit Criteria

- [ ] `devrel demo ideate --context "..." --help` shows all flags
- [ ] `devrel demo run --concept X --help` shows all flags
- [ ] `devrel demo generate --concept X` produces files in demos/ directory
- [ ] `devrel demo test --path demos/X` runs pytest and returns structured result
- [ ] `devrel demo package --path demos/X` produces README.md
- [ ] `devrel demo run --concept X` chains all 3 stages automatically
- [ ] Test failure triggers automatic retry with error context fed back to code gen
- [ ] Retry budget exhaustion stops pipeline and reports failures
- [ ] All tests pass (`pytest tests/ -v -m "not integration"`)
- [ ] `ruff check .` passes with no errors

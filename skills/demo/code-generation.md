---
name: code-generation
description: Code quality standards for generated Mellea demos
category: demo
---

# Code Generation Standards

You are generating runnable Python demo code that showcases Mellea. The code must work out of the box and serve as a learning resource for developers.

## File Structure

Generate exactly these files:
1. **main.py** — the demo script, runnable with `python main.py`
2. **test_demo.py** — basic test file for validation
3. **requirements.txt** — all dependencies with pinned versions

## Code Requirements

- All imports at the top of the file
- Use **actual Mellea APIs** — no hallucinated functions or classes
- Include inline comments explaining each step
- Type hints on all public functions
- Black-compatible formatting (88 char line width)
- No debug prints in final output

## Test File Requirements

The test file (`test_demo.py`) must:
- Import the main module without error
- Call the primary function with sample input
- Assert the output type matches expectations
- Check that no exceptions are raised during normal execution

## requirements.txt

- Pin exact versions (e.g., `mellea==0.4.2`, not `mellea>=0.4`)
- Include all transitive dependencies that are not part of the Python stdlib
- Do not include test dependencies (pytest is assumed to be installed)

## On Repair (retry after test failure)

When you receive `repair_context` with previous error output:
1. Read the error messages carefully
2. Identify the **specific** failure (import error, type mismatch, assertion failure, etc.)
3. Make **minimal targeted changes** to fix only the identified issues
4. Do NOT rewrite the entire demo — preserve working code
5. Add a comment near the fix explaining what was changed and why

## Common Pitfalls

- Forgetting to install dependencies before importing them
- Using APIs that don't exist in the specified Mellea version
- Hardcoding file paths that won't exist on the user's machine
- Using async code without proper event loop setup
- Generating code that only works with a specific model or backend

---
name: packaging
description: README and polish standards for completed demos
category: demo
---

# Demo Packaging Standards

You are polishing a completed, tested demo for public consumption. Your job is to add documentation and clean up — not to change functionality.

## README.md Structure

1. **Title** — demo name as an H1
2. **Overview** — 2-3 sentences: what this demo does, which Mellea feature it showcases
3. **Prerequisites** — Python version, Mellea version, any external dependencies
4. **Installation** — step-by-step (create venv, install requirements)
5. **Usage** — exact command to run (`python main.py`)
6. **Expected Output** — show actual output captured from the test run
7. **How It Works** — brief walkthrough of the code, explaining which Mellea features are used and why
8. **License** — one-line reference

## Code Cleanup Rules

- Remove any debug prints or commented-out code
- Ensure consistent formatting (Black-compatible)
- Add docstrings to the main function(s) only — do not over-document
- Do NOT add features, change behavior, or refactor logic
- Do NOT rename variables or restructure code — packaging is polish only

## Expected Output Section

This is the most important documentation section. Developers want to see what will happen before they run code. Include:
- The exact terminal output from a successful run
- If output is non-deterministic (LLM-generated), show a representative example
- Truncate very long outputs with `...` after the first meaningful portion

## Things to Avoid

- Adding a table of contents for a short README
- Including badges or shields (this is a demo, not a published package)
- Overly long "How It Works" sections — link to Mellea docs for details
- Changing any functional code during packaging

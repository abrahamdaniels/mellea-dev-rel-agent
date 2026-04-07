---
name: ideation
description: How to generate compelling demo concepts for Mellea
category: demo
---

# Demo Ideation

You are generating demo concepts that showcase Mellea's value to developers. Each concept must be a self-contained, runnable Python script that highlights a specific Mellea capability.

## Core Mellea Features to Showcase

- **Structured output validation** — Generating typed, schema-validated responses
- **Requirements** — Enforcing constraints on generated content (length limits, format rules, factual accuracy)
- **Rejection sampling** — Automatically re-generating when requirements fail
- **Instruct-validate-repair** — Feeding validation errors back to the LLM for targeted fixes
- **`@generative` decorator** — Turning Python functions into reliable LLM calls

## Concept Quality Criteria

- Each concept must be **self-contained** — runnable as a single Python script with minimal dependencies
- Target a **specific audience**: ML engineers, backend developers, data scientists, or DevOps engineers
- Use **real-world scenarios**, not toy examples (e.g., "generate a valid SQL migration" not "generate a greeting")
- Prefer concepts that highlight **one Mellea feature clearly** over kitchen-sink demos
- Complexity ratings: **S** = <50 lines, **M** = 50-150 lines, **L** = 150+ lines

## Output Requirements

For each concept, provide:
1. **Title** — concise, descriptive
2. **Description** — 2-3 sentences explaining what the demo does
3. **Target audience** — who would find this useful
4. **Complexity** — S, M, or L
5. **Mellea features** — list of specific features demonstrated
6. **Why this works** — 1 sentence on pedagogical value

## Things to Avoid

- Demos that require API keys or paid services to run
- Demos that need large datasets or model downloads
- Concepts that overlap heavily with each other
- Demos where Mellea's value isn't clear (if plain string output would work just as well, the concept is wrong)

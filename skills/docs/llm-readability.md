---
name: llm-readability
description: What makes documentation LLM-friendly
category: docs
---

# LLM Readability Standards

Documentation that is easy for LLMs to parse is also easy for humans to parse. These standards optimize for both audiences.

## Self-Containment

- Each page should be understandable without reading other pages
- Define terms on first use within each page, even if defined elsewhere
- Include all necessary context inline rather than relying on reading order

## Explicitness

- Spell out types, defaults, and constraints — never assume the reader knows
- Write `timeout (int, default: 30, in seconds)` not just `timeout`
- State what happens when optional parameters are omitted

## Code Examples

- Include expected output alongside input (LLMs use input/output pairs for grounding)
- Show both successful and error cases where relevant
- Every code block should specify the language tag

## Structure

- Use tables for structured data (parameters, options, comparisons), not prose paragraphs
- API signatures in code blocks, not inline formatting
- One concept per page when possible
- Consistent heading patterns across all pages

## Naming

- Use the same term for the same concept everywhere
- Avoid abbreviations unless universally known in the domain
- Function/class/module names in backticks: `generate_structured()`

## Disambiguation

- Avoid ambiguous pronouns: "it", "this", "that" — name the thing explicitly
- Avoid relative references: "the function above", "this module" — use the full name
- Each section should make sense if extracted in isolation

## Actionable Guidance

- Include "when to use" and "when NOT to use" sections for major features
- Document error messages with cause and resolution
- Provide migration paths when APIs change

## Common Anti-Patterns

- Docs that only describe what something IS without showing how to USE it
- Pages that require reading 3 other pages to understand
- Inconsistent parameter naming between docs and actual code
- Missing type information on return values

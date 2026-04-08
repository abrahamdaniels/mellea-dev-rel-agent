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
1. **Explicitly mentions "Mellea"** (the Python library) - not just words containing "mellea" like "malleable"
2. Contains substantive content about the library (not just a name in a list)
3. Is from a real user/developer (not automated/bot content)
4. **Relates to AI reliability, safety, trust, structured outputs, or production AI** - must connect to Mellea's core purpose
5. **Technical context**: Discusses structured output validation, rejection sampling, LLM reliability, or similar technical concepts

## Strict Filtering Rules

**Exclude mentions that:**
- Are about "malleable" anything (bones, memory, gender, etc.)
- Don't explicitly name "Mellea" as the Python library
- Are purely promotional or generic AI discussions
- Lack technical substance or use case discussion
- Are about other tools/projects with similar-sounding names

**Include mentions that:**
- Reference "Mellea" + structured outputs, AI safety, LLM validation
- Discuss production AI reliability challenges
- Compare Mellea to other AI safety/validation tools
- Show practical usage of Mellea for AI trust/reliability
- Mention specific Mellea features (start_session, loop_budget, @generative)

## Quality Gates

- Must contain the exact word "Mellea" (case-insensitive)
- Must relate to AI/LLM reliability, safety, or structured outputs
- Must show technical understanding or practical application

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

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

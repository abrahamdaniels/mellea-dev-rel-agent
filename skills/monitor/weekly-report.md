---
name: weekly-report
description: >-
  How to structure and write the weekly DevRel monitor report.
  Covers metrics presentation, mention analysis, and actionable recommendations.
applies_to: [monitor]
---

# Weekly DevRel Report

Instructions for generating the weekly monitor report.

## Report Structure

1. **Metrics Snapshot** -- GitHub stats (stars, forks, issues) with delta from previous week.
   PyPI download counts with weekly trend. Keep to key numbers, no filler.
2. **Mention Activity** -- Table of mentions grouped by source. Include: source, count,
   average sentiment, most notable mention (with link). Sort by relevance, not count.
3. **Publication Activity** -- Cross-reference with tracked assets from the project board
   (if available). List what was published this period and on which platforms.
4. **Highlights and Recommendations** -- 3-5 bullet points. Each must reference specific
   data from the sections above. No generic advice. Recommendations should be actionable
   ("write a blog post about X because mentions of Y are trending").

## Metrics Presentation Rules

- Always show absolute number AND delta (e.g., "Stars: 1,247 (+23)")
- Use percentage for trends that span multiple weeks
- Round percentages to whole numbers
- If a metric is unavailable, say "N/A" -- never fabricate numbers
- Group related metrics (GitHub metrics together, PyPI together)

## Mention Analysis Rules

- Classify sentiment as: positive, negative, neutral, or mixed
- "Notable" means: high engagement (>10 upvotes/comments), from an influential source,
  or contains specific feedback about Mellea
- Link to the original mention, not a screenshot or summary
- Include the relevant quote (1-2 sentences max) for notable mentions

## Recommendation Quality Gates

- Every recommendation must cite specific data from the report
- "Engagement is up" is not actionable. "Reddit mentions of streaming support grew 3x --
  write a technical blog about the streaming API" is actionable.
- Limit to 3-5 recommendations. More dilutes focus.
- Prioritize by potential impact, not ease of execution

## Common Mistakes

- Padding the report with metrics that haven't changed
- Listing every mention instead of curating the notable ones
- Recommendations that don't connect to the data
- Missing deltas (absolute numbers without context are useless)

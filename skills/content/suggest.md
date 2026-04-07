---
name: content-suggest
description: >-
  How to analyze monitor data and generate prioritized content
  recommendations. Bridges the monitor and content workstreams.
applies_to: [content]
---

# Content Suggest

Instructions for identifying and prioritizing content opportunities
from monitor data and recent project activity.

## Input Analysis

You will receive:
1. Latest monitor brief (mentions, sentiment, trends)
2. Recent GitHub releases and PRs (from context resolver)
3. Optional additional context from the user

## Opportunity Identification Rules

Look for these content triggers (in priority order):
1. **New release or major PR merged** -- always worth content. Check if it's already
   been written about.
2. **Trending mentions** -- mentions growing week-over-week, especially positive or
   mixed (mixed = opportunity to shape narrative).
3. **Feature requests** -- recurring asks in mentions = opportunity for "how to" or
   "roadmap" content.
4. **Competitor comparisons** -- mentions comparing Mellea to other tools = opportunity
   to highlight differentiators.
5. **Community questions** -- repeated questions = documentation or blog opportunity.

## Recommendation Format

For each opportunity, specify:
- **Topic**: Clear, specific (not "write about streaming" but "streaming API performance
  benchmarks vs. synchronous calls")
- **Why now**: What data triggered this recommendation (cite specific mention, release, or metric)
- **Recommended format**: social_post, technical_blog, blog_outline, personal_blog, or demo
- **Recommended tone**: personal or ibm (based on target audience and platform)
- **Context to use**: Specific --context value the user should pass to the content agent

## Prioritization Rules

- New releases > trending mentions > feature requests > competitor comparisons > questions
- High-sentiment mentions boost priority
- Content that fills a gap (feature exists, no content about it) ranks higher
- Limit to 5 recommendations max

## Common Mistakes

- Suggesting content about features that are still in development
- Recommending the same format for every opportunity
- Not providing specific --context values (the user should be able to copy-paste)
- Suggesting content that was already published (check publication activity in the brief)

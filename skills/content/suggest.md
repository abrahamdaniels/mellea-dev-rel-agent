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

## Step 1: Filter Mentions

FIRST, apply the mention-evaluation criteria to filter out irrelevant mentions:
- Only consider mentions that EXPLICITLY mention "Mellea" (not "malleable" or similar words)
- Must relate to AI reliability, safety, trust, structured outputs, or production AI
- Exclude mentions about gender, sports, memory, bones, or any non-AI topics
- If no relevant mentions remain, focus on GitHub activity and feature status instead

## Step 2: Opportunity Identification

Look for these content triggers (in priority order), focusing on AI security, safety, trust, structured outputs, and reliable AI agents:
1. **New release or major PR merged** -- always worth content. Check if it's already been written about.
2. **Trending mentions in AI security/safety/trust** -- mentions growing week-over-week about structured outputs, reliable agents, AI safety concerns, trust issues with LLMs
3. **Feature requests for reliability** -- recurring asks for structured validation, safety constraints, trust mechanisms
4. **Competitor comparisons in reliability space** -- mentions comparing Mellea to other tools for AI safety, structured outputs, or reliable agents
5. **Community questions about AI trust/safety** -- repeated questions about LLM reliability, structured outputs, safety constraints

## Content Theme Alignment

All opportunities must align with these core themes:
- **AI Security**: Preventing harmful outputs, safety constraints, secure AI deployment
- **AI Safety**: Avoiding hallucinations, ensuring reliable outputs, safety guardrails
- **AI Trust**: Building confidence in AI systems, verifiable outputs, reliability
- **Structured Outputs**: Schema validation, type safety, predictable AI responses
- **Reliable AI Agents**: Consistent behavior, error handling, production-ready AI systems

Related keywords to monitor: "LLM safety", "AI reliability", "structured generation", "output validation", "trustworthy AI", "AI guardrails", "production AI", "enterprise AI"

## Recommendation Format

For each opportunity, specify:
- **Topic**: Clear, specific (not "write about streaming" but "streaming API performance
  benchmarks vs. synchronous calls")
- **Why now**: What data triggered this recommendation (cite specific mention, release, or metric)
- **Recommended format**: social_post, technical_blog, blog_outline, personal_blog, or demo
- **Why this format**: Explain why this format is best for the topic and audience (e.g., "technical_blog for detailed implementation guidance")
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

---
name: social-post
description: >-
  How to write social media posts (Twitter/X and LinkedIn) promoting Mellea
  features, demos, or blog posts. Covers structure, what makes posts work,
  and output format.
applies_to: [content]
---

# Social Post Writing Guide

This skill covers writing social media posts about Mellea. A good social post makes one clear point, gives the reader a reason to care, and ends with a reason to click or engage.

## The Anatomy of a Good Post

1. **Hook (first line)**: The only line many people will read. Make it count.
   - Concrete observation beats abstract claim
   - Problem → solution beats feature announcement
   - Specific beats vague: "3 lines of code" beats "easy to use"

2. **Body (1-3 sentences or lines)**: Expand the hook with evidence or context.
   - Code snippet, number, or comparison
   - The "so what" — why does this matter?

3. **CTA (optional)**: Link, repo, or engagement hook ("What's your approach?")

## What Makes a Post Work

| Works | Doesn't Work |
|---|---|
| "LLM output broke my parser. Fixed it with Mellea in 3 lines." | "Excited to announce Mellea v0.9 with structured output validation!" |
| "New in Mellea: pass a Pydantic model, get a validated object back." | "Mellea provides enterprise-grade reliability for LLM pipelines." |
| "Tried switching from Ollama to OpenAI — changed one argument." | "Mellea supports multiple backends for flexibility and scalability." |

## Output Format

For each requested platform, produce the post in this format:

```
[PLATFORM: twitter | linkedin]

[POST TEXT]

---
Character count: [N]
Hashtags used: [list or "none"]
```

If platform is "both", produce two separate blocks.

## Self-Review Checklist

Before outputting a post:
- [ ] Does the first line work as a standalone statement?
- [ ] Is there at least one concrete detail (number, line of code, comparison)?
- [ ] Is it free of superlatives ("revolutionary", "game-changing")?
- [ ] Does it fit the platform character limit?
- [ ] Would I actually post this?

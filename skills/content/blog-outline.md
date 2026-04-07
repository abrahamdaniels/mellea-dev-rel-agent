---
name: blog-outline
description: >-
  How to produce a structured IBM Research blog skeleton. Output is an
  outline with section headers and bullet points, not full prose.
applies_to: [content]
---

# IBM Research Blog Outline Guide

This skill produces structured outlines for IBM Research blog posts about Mellea. The output is a skeleton — section headers with 2-3 bullet points each — not a full article. A human fills in the prose.

## Target Audience

IBM Research blog readers are:
- Enterprise developers evaluating structured output solutions
- AI/ML team leads making technology decisions
- Researchers interested in reliability and validation techniques

## Required Outline Structure

Every outline must contain these three sections:

### 1. What It Is
- One-sentence definition of the feature or capability
- What problem it solves (framed for enterprise context)
- How it relates to the broader Mellea library

### 2. Why It Matters
- The business or technical pain point it addresses
- What breaks or degrades without this capability
- Competitive context: how this compares to alternatives

### 3. How To Use It
- Prerequisites (install, config)
- Core API call or pattern (pseudocode-level, not full code)
- Expected output or result

## Additional Required Elements

- **Title suggestions:** Provide 2-3 title options. IBM Research titles are descriptive and specific, not clickbait.
- **Target audience note:** One sentence describing who should read this post.
- **Suggested length:** Estimate for the final blog (typically 600-1000 words).
- **Key Mellea features:** List the specific APIs or patterns referenced.

## Output Format

```markdown
# Blog Outline: {working title}

**Target audience:** {one sentence}
**Suggested length:** {word count range}
**Key Mellea features:** {comma-separated list}

## Title Options
1. {option 1}
2. {option 2}
3. {option 3}

## What It Is
- {bullet 1}
- {bullet 2}
- {bullet 3}

## Why It Matters
- {bullet 1}
- {bullet 2}
- {bullet 3}

## How To Use It
- {bullet 1}
- {bullet 2}
- {bullet 3}
```

## Common Mistakes

- Writing full prose paragraphs instead of bullets
- Making bullets too vague ("It's useful for many things")
- Missing the audience note — the person filling in the outline needs to know who they're writing for
- Using technical jargon without defining it (remember: the reader may be a team lead, not a developer)
- Suggesting titles that sound like marketing copy instead of technical content

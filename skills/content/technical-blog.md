---
name: technical-blog
description: >-
  How to write a HuggingFace-style technical blog post about a Mellea feature
  or release. Covers structure, code examples, audience expectations, and
  HuggingFace-specific frontmatter.
applies_to: [content]
---

# Technical Blog Writing Guide (HuggingFace Style)

This skill covers writing technical blog posts in the HuggingFace style — developer-first, code-heavy, reproducible, and focused on a single clear capability.

## HuggingFace Blog Audience

HuggingFace readers are:
- ML engineers and applied researchers
- Python developers comfortable with PyTorch, transformers, and Pydantic
- Interested in running models locally (Ollama, vLLM) or via API
- Skeptical of marketing; they want to see working code

Write for someone who will open a terminal and try your code before finishing the post.

## HuggingFace Frontmatter Format

Every HuggingFace blog post starts with YAML frontmatter:

```yaml
---
title: "Title of the Post"
thumbnail: /blog/assets/your-post-slug/thumbnail.png
authors:
  - user: your_hf_username
---
```

Include this at the top of the draft. Use a descriptive, specific title — not a marketing headline.

## Required Post Structure

Every technical blog post must contain these sections in this order:

### 1. Hook (no heading, 1-3 sentences)
The first paragraph before any heading. States the problem or capability directly. No "In this post, we will..." — just the thing itself.

### 2. Motivation (## The Problem / ## Why This Matters)
2-4 paragraphs. Why does this problem exist? What breaks without this solution? Use a concrete failure mode or before/after comparison. Code showing the broken/awkward state is effective here.

### 3. The Solution / How It Works (## How [Feature Name] Works)
The core of the post. Walk through the capability step by step. Every claim must be backed by working code. Use inline code for single expressions; use fenced code blocks for anything 2+ lines.

### 4. Code Walkthrough (## Example / ## Walkthrough)
Complete, runnable example. Must include:
- Import statements
- Setup (model loading, session creation)
- The core usage
- What the output looks like (as a comment or separate block)

### 5. Trade-offs and Limitations (## When to Use This / ## Limitations)
Be honest. What doesn't this solve? What are the performance characteristics? When should someone reach for a different approach? This section builds credibility.

### 6. Call to Action (## Get Started / ## Try It)
- Link to the GitHub repo
- Install command: `pip install mellea`
- Link to docs or notebook (if available)
- Invitation to contribute or open issues

## Code Example Rules

- **All code must be syntactically correct and runnable**
- Use Python 3.11+ syntax (type hints with `|`, `match` statements are fine)
- Fenced code blocks must specify the language: ` ```python ` not ` ``` `
- Don't abbreviate: no `...` as a stand-in for real code unless it's a method stub
- Output blocks use `# Output:` comment followed by the expected output
- Keep examples focused: one concept per block

```python
# Good: focused, complete, shows the output
from mellea import generative
from pydantic import BaseModel

class Sentiment(BaseModel):
    label: str  # "positive", "negative", "neutral"
    confidence: float

@generative(backend="ollama", model="granite-3.3-8b")
def classify(text: str) -> Sentiment:
    """Classify the sentiment of: {text}"""
    ...

result = classify("The structured output feature saved me hours of debugging.")
# Output: Sentiment(label='positive', confidence=0.94)
```

## HuggingFace-Specific Guidance

- **Model-centric framing**: Connect to specific models where relevant. "Works with Granite 3.3, Llama 3, and Mistral" is more useful than "works with any Ollama model."
- **Reproducibility**: Include model versions, library versions, and hardware specs for benchmarks.
- **Notebooks**: If the feature benefits from interactive exploration, mention that a Colab/HF Space is available (or that one should be created).
- **Dataset cards**: If the feature involves data, reference HF datasets by their hub ID.
- **Community angle**: HuggingFace readers contribute back. Explicitly invite PRs or feedback.

## Length and Pacing

- Target: 800-1,500 words
- Short paragraphs (3-4 sentences max)
- Every heading should introduce something new — no heading that just says "Introduction"
- If a section runs more than 400 words without a code example, add one

## Self-Review Checklist

Before outputting the draft, verify:
- [ ] Frontmatter is present and correctly formatted
- [ ] Post opens with the capability, not background
- [ ] All code blocks have a language tag
- [ ] The complete example is runnable (no `...` shortcuts)
- [ ] Trade-offs section is honest, not just cautionary boilerplate
- [ ] CTA includes install command and GitHub link
- [ ] No Tier 1 LLM-tell phrases (see de-llmify skill)
- [ ] Total length is 800-1,500 words

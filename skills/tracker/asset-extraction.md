---
name: asset-extraction
description: How to extract metadata from published DevRel assets
category: tracker
---

# Asset Metadata Extraction

You are extracting structured metadata from a published DevRel asset. Your goal is to create a complete, accurate record for tracking purposes.

## Fields to Extract

1. **Asset type** — one of: `blog`, `social_post`, `ibm_article`, `demo`, `talk`
2. **Title** — the most descriptive title for the asset (not necessarily the page title)
3. **Feature** — the specific Mellea capability this asset covers (e.g., "structured output", "rejection sampling", "streaming")
4. **Sentiment** — one of: `positive`, `negative`, `neutral`, `mixed`

## Extraction Guidelines

- **Asset type**: Infer from the platform and content format. Social media posts are `social_post`, long-form articles are `blog` or `ibm_article` depending on the publisher, code repositories are `demo`, presentations are `talk`.
- **Title**: Use the actual content title if available. For social posts, use the first sentence or main topic as the title. Keep it under 80 characters.
- **Feature**: Map to a specific Mellea capability when possible. Common features: structured output, requirements, rejection sampling, instruct-validate-repair, @generative decorator, streaming, multi-backend support. If the asset covers multiple features, pick the primary one.
- **Sentiment**: Classify the overall tone. Positive = praise, recommendation, success story. Negative = complaint, bug report, criticism. Neutral = documentation, tutorial, announcement. Mixed = contains both positive and negative elements.

## Edge Cases

- If the content is behind a paywall or login, extract what you can from the URL and any visible metadata
- If the asset is in a non-English language, still extract metadata based on available information
- For demos, the feature should be the primary Mellea feature the demo showcases

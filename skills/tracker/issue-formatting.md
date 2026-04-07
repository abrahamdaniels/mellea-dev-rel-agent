---
name: issue-formatting
description: GitHub issue structure for tracked assets
category: tracker
---

# Asset Tracking Issue Format

You are formatting a GitHub issue to record a tracked DevRel asset.

## Issue Title Format

```
[Asset] {type}: {title}
```

Examples:
- `[Asset] blog: Getting Started with Mellea Structured Output`
- `[Asset] social_post: Mellea 0.5 release announcement`
- `[Asset] demo: Streaming validation pipeline`

## Issue Body Format

Use this exact table structure:

```markdown
## Asset Tracking

| Field | Value |
|---|---|
| Type | {asset_type} |
| Feature | {feature} |
| Title | {title} |
| Date | {date} |
| Sentiment | {sentiment} |
| Location | {link} |
| Platform | {platform} |
```

## Labels

Apply these labels:
- `asset-tracking` (always)
- `type:{asset_type}` (e.g., `type:blog`, `type:social_post`)

## Guidelines

- Keep descriptions concise — the issue is a record, not a review
- Include the original URL prominently so the asset can be found later
- Use ISO date format (YYYY-MM-DD)
- If a feature cannot be determined, use "general"

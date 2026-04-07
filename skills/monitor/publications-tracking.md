---
name: publications-tracking
description: How to evaluate DevRel publication performance from available data
category: monitor
---

# Publications Performance Tracking

You are analyzing the performance and coverage of published DevRel assets for the Mellea project. Your data sources are GitHub issues (tracked assets) and monitor briefs (mentions and engagement signals).

## What Data Is Available

- **Tracked assets:** GitHub issues labeled `asset-tracking`, each containing type, feature, title, date, sentiment, link, and platform
- **Mention data:** From monitor briefs, showing where Mellea is being discussed and with what sentiment
- **Weekly report data:** GitHub stats (stars, forks), PyPI downloads, mention counts

## Metrics to Evaluate

### Coverage Metrics
- Asset count by type (blog, social_post, demo, talk, ibm_article)
- Asset count by feature (which Mellea features have coverage)
- Coverage gaps: features with no published assets
- Recency: how old is the newest asset per feature

### Cross-Reference Metrics
- Which published assets appear in mentions (organic amplification)
- Which mentioned topics have no published assets (missed opportunities)
- Platform distribution: are we publishing on all target platforms?

### Trend Indicators
- Publication velocity: assets per week/month
- Type distribution trend: are we favoring one format over others?
- Feature coverage trend: are new features getting covered promptly?

## Report Structure

```markdown
# Publications Performance Report - {date}

## Summary
{2-3 sentences on overall publication health}

## Asset Inventory
| Type | Count | Latest | Coverage |
|---|---|---|---|
{row per asset type}

## Feature Coverage
| Feature | Assets | Last Published | Gap? |
|---|---|---|---|
{row per feature}

## Cross-Reference: Publications vs Mentions
- {observations about which assets got organic traction}
- {observations about mentioned topics without published assets}

## Recommendations
1. {highest priority action}
2. {second priority action}
3. {third priority action}
```

## Guidelines

- Be specific in recommendations: "Write a blog post about streaming validation" not "Consider more content"
- Flag stale features: if a feature's newest asset is > 30 days old, note it
- Don't fabricate metrics — if data is unavailable, say so
- Cross-reference mentions with publications to find organic amplification signals

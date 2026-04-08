---
name: feature-tracking
description: >-
  How to determine what Mellea features are available, in development,
  or planned based on GitHub repository analysis.
applies_to: [content, monitor, docs]
---

# Feature Tracking

Instructions for determining Mellea project features and development status.

## Feature Status Determination

### Available Features (Released)
- **Source**: GitHub releases, PyPI package, documentation
- **Indicators**: Tagged releases, version bumps, changelog entries
- **Verification**: Check `mellea/__init__.py` exports, README examples

### In Development Features (PRs/Issues)
- **Source**: Open PRs, GitHub issues labeled "enhancement" or "feature"
- **Indicators**: Active branches, draft PRs, issue discussions
- **Status**: "In development" if PR exists, "Planned" if issue only

### Planned Features (Roadmap)
- **Source**: GitHub issues, project boards, milestone planning
- **Indicators**: Issues with "future" or "roadmap" labels

## Feature Categories

### Core Reliability Features
- Structured output validation
- Rejection sampling (`loop_budget`)
- Multi-backend support (Ollama, OpenAI, Anthropic)
- Requirements system
- Session management

### Advanced Features
- `@generative` decorator
- Streaming support
- Custom validation rules
- Error handling improvements
- Performance optimizations

### Enterprise Features
- Audit logging
- Compliance features
- Multi-tenant support
- Advanced security controls

## Verification Methods

### Code Analysis
- Check `mellea/` directory structure
- Review `__init__.py` exports
- Examine test files for feature coverage

### Documentation Review
- Check `docs/` for feature documentation
- Review examples and tutorials
- Verify API reference completeness

### GitHub Analysis
- Scan open PRs for new features
- Review issues for feature requests
- Check project board for roadmap items

## Content Guidelines

When writing about features:
- **Available**: Use present tense, provide examples
- **In development**: Use future tense, note "coming soon"
- **Planned**: Use conditional tense, note "under consideration"

Never write about unreleased features as if they're available.</content>
<parameter name="filePath">/Users/abrahamdaniels/Mellea/mellea-devrel/skills/shared/feature-tracking.md
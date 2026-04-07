---
name: review-criteria
description: How to evaluate existing documentation quality
category: docs
---

# Documentation Review Criteria

You are reviewing existing documentation for quality, accuracy, and LLM-readability. Classify each finding by severity and category.

## Severity Levels

### Critical (must fix)

These findings indicate the docs are actively misleading or broken:

- API signature in docs doesn't match actual code
- Code example has syntax errors or missing imports
- Feature documented but removed from codebase
- Broken cross-references or dead links
- Security-sensitive information exposed in examples
- Instructions that would cause data loss if followed

### Warning (should fix)

These findings reduce docs quality but don't actively mislead:

- Missing code examples for documented features
- Parameters listed without types or defaults
- Prose that uses ambiguous pronouns or relative references
- Pages exceeding 500 lines without clear section breaks
- Outdated version numbers or dependency references
- Missing error handling guidance for common failure modes

### Info (nice to fix)

These findings are improvement opportunities:

- Missing "when to use" guidance
- Code examples without expected output
- Inconsistent terminology across pages
- Missing cross-references to related features
- Sections that could benefit from a table instead of prose
- Missing page purpose statement

## Finding Categories

Use these category labels:

| Category | Description |
|---|---|
| stale_api | API signature or behavior doesn't match code |
| missing_example | Feature documented without code example |
| broken_link | Cross-reference or URL doesn't resolve |
| ambiguous_reference | Pronouns or relative references that need context |
| missing_types | Parameters or returns without type information |
| syntax_error | Code example has syntax or import errors |
| removed_feature | Docs reference a feature no longer in the codebase |
| missing_section | Expected section (e.g., error handling) is absent |
| inconsistent_naming | Same concept called different names across pages |
| structure | Page organization issues (too long, no headers, etc.) |

## Review Process

1. Read each file completely before reporting findings
2. Cross-check API signatures against provided source code when available
3. Verify code examples mentally for syntax and import correctness
4. Check that cross-references point to real pages/sections
5. Assess overall page structure and self-containment
6. Report specific line ranges when possible for targeted fixes

## Output Guidelines

- Be precise: "missing import for `datetime` in example on line 45" not "some imports are missing"
- One finding per issue — don't combine multiple problems
- Include a concrete suggestion for each finding when possible
- Prioritize critical findings over volume of info findings
- False positives waste reviewer time — when uncertain, downgrade severity

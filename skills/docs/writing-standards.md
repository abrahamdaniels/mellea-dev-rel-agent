---
name: writing-standards
description: Documentation writing style guide for Mellea
category: docs
---

# Documentation Writing Standards

You are writing or updating technical documentation for the Mellea project. Follow these standards to produce clear, accurate, and maintainable docs.

## Voice and Tense

- Use active voice, present tense: "Mellea validates the output" not "The output will be validated by Mellea"
- Lead with what the user can DO, not what the feature IS
- Address the reader directly: "you" not "the user"

## Page Structure

- Every page starts with a one-sentence purpose statement
- Heading hierarchy: H1 = page title (one per page), H2 = major sections, H3 = subsections
- No more than 3 heading levels per page
- Keep paragraphs under 4 sentences

## Code Examples

- Code examples must be complete and runnable (include all imports)
- Show the simplest use case first, then advanced options
- Include expected output as a comment or separate block
- Use realistic variable names, not `foo` or `bar`

## API Documentation

- Parameters documented in a table: name, type, default, description
- Return types documented explicitly with example values
- Include at least one complete usage example per public function
- Document exceptions/errors that callers should handle

## Cross-References

- Use explicit file paths: "[see Configuration](docs/configuration.md)" not "see above"
- Never use relative pronouns to reference other sections ("the function mentioned earlier")
- Link to specific sections when possible, not just pages

## Progressive Disclosure

- Start with the 80% use case
- Put advanced configuration, edge cases, and internals in separate sections at the end
- Use collapsible sections or "Advanced" headers for optional depth

## Common Mistakes

- Writing "comprehensive" docs that bury the simple case in caveats
- Documenting internal implementation details that users don't need
- Missing imports in code examples (the #1 frustration for readers)
- Using different terms for the same concept in different pages

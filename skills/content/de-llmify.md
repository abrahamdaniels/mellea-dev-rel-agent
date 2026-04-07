---
name: de-llmify
description: >-
  Post-processing pass to remove LLM-tell patterns from generated content.
  Apply to all drafts before output. Eliminates filler phrases, corporate
  hedging, and structural patterns that signal AI-generated text.
applies_to: [content]
---

# De-LLMify: Removing AI-Generated Text Patterns

Apply this pass to every draft. The goal is content that reads as if a competent human wrote it — not a language model trying to sound helpful.

## Tier 1: Always Remove (Kill on Sight)

These words and phrases are the clearest LLM tells. Delete or rewrite any sentence containing them:

**Filler openers:**
- "Certainly!", "Absolutely!", "Of course!", "Sure!", "Great question!"
- "I'd be happy to...", "I'm glad you asked..."

**Hollow transitions:**
- "It's worth noting that..."
- "It's important to mention that..."
- "It goes without saying that..."
- "Needless to say..."
- "That being said..."

**Corporate hedging:**
- "In today's fast-paced world..."
- "In the ever-evolving landscape of..."
- "At the end of the day..."
- "Moving forward..."
- "Going forward..."

**Empty intensifiers:**
- "Truly", "literally" (unless literal), "very unique", "extremely important"
- "Game-changing", "revolutionary", "paradigm-shifting", "transformative"
- "Cutting-edge", "state-of-the-art" (unless citing a paper benchmark)
- "Seamless", "robust", "powerful", "innovative"

**Sycophantic conclusions:**
- "I hope this helps!"
- "Feel free to reach out if you have any questions!"
- "Don't hesitate to..."
- "Let me know if you need anything else!"

## Tier 2: Rewrite (Context-Dependent)

These patterns appear frequently in LLM output and often indicate weak writing. Rewrite unless there's a specific reason to keep them:

**Excessive hedging:**
- "may or may not", "might potentially", "could possibly"
- Rewrite: pick a stance or qualify with specifics ("in benchmarks", "in our testing")

**Generic lists without substance:**
- "There are many benefits, including: [vague list]"
- Rewrite: pick the two most important, explain why they matter

**Passive voice used to avoid specificity:**
- "It has been observed that..." → "We found that..." or just state the finding
- "This can be used to..." → "Use this to..."

**Throat-clearing openings:**
- First sentence restates the topic without adding information
- Rewrite: start with the first sentence that says something new

## Structural Checks

After removing Tier 1 and rewriting Tier 2:

1. **Does the opening sentence carry weight?** If not, delete it and start with the second sentence.
2. **Is every paragraph earning its place?** If a paragraph could be cut without losing meaning, cut it.
3. **Are there consecutive sentences that say the same thing differently?** Keep the cleaner one.
4. **Does the conclusion add information?** If it only summarizes, shorten it drastically.

## Tone Calibration

After structural checks, read the piece aloud (or simulate doing so). Ask:
- Does this sound like a specific person wrote it, or a template?
- Are there any places where the writing is more formal than it needs to be?
- Are there hedges that could be replaced with a direct claim?

## What NOT to Change

- Technical accuracy: don't simplify terms to sound "more human" if the technical term is correct
- Examples and code: these are usually the most human-like part of LLM output; don't touch them
- Style choices made for the tone (personal vs. IBM): keep those intact

---
name: sentiment-scoring
description: >-
  How to classify sentiment in mentions of Mellea across platforms.
  Used by the monitor agent for mention analysis.
applies_to: [monitor]
---

# Sentiment Scoring

Instructions for classifying the sentiment of mentions.

## Classification Labels

- **positive** -- Praise, enthusiasm, successful usage reports, recommendations to others,
  excitement about features. Examples: "mellea saved us hours", "love the new streaming API"
- **negative** -- Complaints, bug reports, frustration, unfavorable comparisons.
  Examples: "mellea crashed on our dataset", "why doesn't mellea support X?"
- **neutral** -- Factual mentions without emotional valence. Examples: "mellea released v0.8",
  "here's a list of LLM tools: ... mellea ..."
- **mixed** -- Contains both positive and negative signals. Examples: "mellea's API is great
  but the docs are lacking", "fast but unstable"

## Scoring Rules

- Score based on the author's expressed sentiment, not your opinion of the content
- Bug reports are negative even if politely worded
- Feature requests are neutral unless accompanied by frustration
- Comparisons are scored based on whether Mellea comes out favorably
- If the mention is primarily about another tool and Mellea is mentioned in passing,
  score based on how Mellea is characterized in that context
- Sarcasm should be interpreted (e.g., "great, another framework" is negative)

## Confidence

When sentiment is ambiguous, prefer "mixed" over guessing. The report consumer
can read the original mention and make their own judgment.

## Output Format

Return exactly one of: positive, negative, neutral, mixed

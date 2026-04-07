---
name: mellea-knowledge
description: >-
  Core knowledge about the Mellea Python library: what it is, what it does,
  key features, API surface, and common mistakes to avoid when describing it.
applies_to: [content, monitor, demo, docs]
---

# Mellea Knowledge Base

Mellea is a Python library for building reliable LLM-powered applications. It provides structured output validation, rejection sampling, and a consistent interface for multiple LLM backends. Use this knowledge whenever writing about Mellea.

## What Mellea Is

Mellea is a **reliability layer for LLM outputs**. It sits between your application code and the LLM backend, ensuring that outputs match the structure and constraints your application expects.

Key capabilities:
- **Structured output validation**: Use Pydantic models to define the expected output shape. Mellea enforces the schema.
- **Rejection sampling**: If the LLM output doesn't satisfy constraints, Mellea retries automatically (configurable budget).
- **Multi-backend support**: Works with Ollama, OpenAI, Anthropic, and other backends through a unified API.
- **Requirements system**: Declarative constraints (character limits, required fields, format rules) validated at generation time.
- **Session model**: `mellea.start_session()` provides a context manager that encapsulates backend configuration.

## Core API

```python
import mellea
from pydantic import BaseModel

class SocialPost(BaseModel):
    text: str
    hashtags: list[str]

# Structured generation with requirements
with mellea.start_session(backend="ollama", model="granite-3.3-8b") as session:
    post = session.instruct(
        prompt="Write a tweet about our new streaming API",
        format=SocialPost,
        requirements=["text must be under 280 characters"],
        loop_budget=3,  # retry up to 3 times
    )

print(post.text)        # validated string
print(post.hashtags)    # validated list
```

## The @generative Decorator

For functions that return LLM-generated structured data:

```python
from mellea import generative
from pydantic import BaseModel

class BlogOutline(BaseModel):
    title: str
    sections: list[str]
    hook: str

@generative(backend="ollama", model="granite-3.3-8b")
def generate_outline(topic: str) -> BlogOutline:
    """Generate a blog outline for {topic}."""
    ...

outline = generate_outline("streaming APIs in Python")
# outline is a validated BlogOutline instance
```

## Key Terminology

- **Backend**: The LLM provider (ollama, openai, anthropic, etc.)
- **Session**: A context manager that holds backend config for a sequence of calls
- **instruct()**: The primary method for generating structured output
- **loop_budget**: Maximum number of retries for rejection sampling
- **requirements**: List of string constraints evaluated against each generated output
- **@generative**: Decorator for functions whose return type defines the output schema

## What Mellea Is NOT

- Not a prompt engineering framework (no chain-of-thought, few-shot, or RAG utilities)
- Not an agent framework (no tool calling, memory, or multi-step planning)
- Not a fine-tuning library (inference only)
- Not a model router (you pick the backend explicitly)
- Not a caching layer (though you can cache session results yourself)

## Positioning

When writing about Mellea, emphasize:
1. **Reliability**: LLM outputs can fail in subtle ways. Mellea catches these failures automatically.
2. **Simplicity**: The API is small. `start_session()` + `instruct()` covers 90% of use cases.
3. **Backend agnosticism**: Switch from Ollama to OpenAI by changing one parameter.
4. **Pythonic**: Output types are plain Pydantic models. No special Mellea types to learn.

## Common Mistakes to Avoid

- Don't say "Mellea generates text" — it validates and structures LLM-generated text
- Don't confuse `loop_budget` with token limits — it's about retry attempts, not token count
- Don't describe Mellea as an LLM — it's a library that wraps LLMs
- Don't imply Mellea writes prompts for you — you write the prompt, Mellea validates the output

from __future__ import annotations

import pytest

from agents.demo import parse_concept_file

SAMPLE_CONCEPTS = """\
# Demo Concepts - 2024-04-06

**Source:** Streaming API

---

## Concept 1: Streaming Validator

**Description:** A demo that validates streaming output in real-time.
**Target audience:** Backend developers
**Complexity:** M

---

## Concept 2: Schema Enforcer

**Description:** Enforces JSON schema on LLM output.
**Target audience:** ML engineers
**Complexity:** S

---

## Concept 3: Retry Demo

**Description:** Shows instruct-validate-repair loop.
**Target audience:** Data scientists
**Complexity:** L
"""


def test_file_with_selector_returns_concept(tmp_path):
    concept_file = tmp_path / "concepts.md"
    concept_file.write_text(SAMPLE_CONCEPTS)

    result = parse_concept_file(f"{concept_file}:2")
    assert "Schema Enforcer" in result
    assert "Streaming Validator" not in result


def test_file_without_selector_returns_full_content(tmp_path):
    concept_file = tmp_path / "concepts.md"
    concept_file.write_text(SAMPLE_CONCEPTS)

    result = parse_concept_file(str(concept_file))
    assert "Concept 1" in result
    assert "Concept 2" in result
    assert "Concept 3" in result


def test_non_file_input_returns_raw_text():
    raw = "Build a demo showing structured output validation"
    result = parse_concept_file(raw)
    assert result == raw


def test_invalid_selector_raises(tmp_path):
    concept_file = tmp_path / "concepts.md"
    concept_file.write_text(SAMPLE_CONCEPTS)

    with pytest.raises(ValueError, match="not found"):
        parse_concept_file(f"{concept_file}:99")


def test_first_concept_extracted(tmp_path):
    concept_file = tmp_path / "concepts.md"
    concept_file.write_text(SAMPLE_CONCEPTS)

    result = parse_concept_file(f"{concept_file}:1")
    assert "Streaming Validator" in result
    assert "Schema Enforcer" not in result

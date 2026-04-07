from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator


class ContextSource(BaseModel):
    # source_type: github_pr, github_issue, github_release, web, file, text, brief
    source_type: str
    origin: str       # Original input string
    title: str | None = None
    content: str
    metadata: dict = {}


class ContextBlock(BaseModel):
    sources: list[ContextSource]
    combined_text: str = ""
    metadata: dict = {}

    @model_validator(mode="after")
    def assemble_combined_text(self) -> "ContextBlock":
        if not self.combined_text and self.sources:
            parts = []
            for source in self.sources:
                header = f"## Source: {source.source_type} - {source.title or source.origin}"
                parts.append(f"{header}\n\n{source.content}")
            self.combined_text = "\n\n---\n\n".join(parts)
        return self


class DraftOutput(BaseModel):
    agent_name: str
    content: str
    file_path: str | None = None
    metadata: dict = {}


class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_base_seconds: float = 1.0
    backoff_multiplier: float = 2.0


# --- Monitor models (Phase 2) ---


class Mention(BaseModel):
    """A single mention of the project on an external platform."""
    source: str             # "reddit", "hackernews", "github_discussions", "pypi"
    title: str | None = None
    content: str
    url: str
    author: str | None = None
    timestamp: datetime
    score: int | None = None
    sentiment: str | None = None  # Filled by sentiment classification
    metadata: dict = {}


class SentimentResult(BaseModel):
    """Structured output for sentiment classification."""
    sentiment: Literal["positive", "negative", "neutral", "mixed"]


# --- Demo models (Phase 3) ---


@dataclass
class TestResult:
    """Structured test result from the demo test runner (not LLM-generated)."""
    __test__ = False  # Prevent pytest collection

    passed: bool
    total_tests: int
    failed_tests: int
    error_output: str | None = None
    failing_test_names: list[str] = field(default_factory=list)


class DemoConcept(BaseModel):
    """A single demo concept produced by the ideation agent."""
    title: str
    description: str
    target_audience: str
    complexity: Literal["S", "M", "L"]
    mellea_features: list[str]
    why_this_works: str


# --- Tracker models (Phase 4) ---


class AssetMetadata(BaseModel):
    """Metadata for a tracked DevRel asset."""
    asset_type: str          # blog, social_post, ibm_article, demo, talk
    title: str
    feature: str | None = None
    date: str                # ISO date string
    sentiment: str | None = None
    link: str
    platform: str | None = None


class AssetExtractionResult(BaseModel):
    """Structured output from LLM-based asset metadata extraction."""
    asset_type: Literal[
        "blog", "social_post", "ibm_article", "demo", "talk"
    ]
    title: str
    feature: str
    sentiment: Literal["positive", "negative", "neutral", "mixed"]


# --- Docs models (Phase 5) ---


class DocFinding(BaseModel):
    """A single finding from documentation review."""
    file_path: str
    severity: Literal["critical", "warning", "info"]
    category: str              # e.g., "stale_api", "missing_example", "broken_link"
    description: str
    suggestion: str | None = None


class DocReviewReport(BaseModel):
    """Aggregate output from a docs review pass."""
    files_reviewed: int
    findings: list[DocFinding]
    summary: str


class DocUpdatePlan(BaseModel):
    """Structured plan for which doc files to update."""
    affected_files: list[str]
    reason: str
    change_type: Literal["update", "create", "deprecate"]


class ContentSuggestion(BaseModel):
    """A single content opportunity identified by the suggest agent."""
    topic: str
    why_now: str
    recommended_format: str   # "social_post", "technical_blog", "blog_outline", "demo"
    recommended_tone: str     # "personal", "ibm"
    context_reference: str    # PR URL, brief reference, or mention link
    priority: int             # 1 = highest

"""Tests for the Publications Tracker agent."""
from unittest.mock import patch

from core.models import DraftOutput

SAMPLE_REPORT = """# Publications Performance Report - 2026-04-07

## Summary

The Mellea DevRel program has 5 tracked assets across 3 types. Blog posts
dominate the mix; social and demo coverage is thin.

## Asset Inventory
| Type | Count | Latest | Coverage |
|---|---|---|---|
| blog | 3 | 2026-03-20 | Good |
| social_post | 1 | 2026-02-15 | Low |
| demo | 1 | 2026-01-10 | Low |

## Feature Coverage
| Feature | Assets | Last Published | Gap? |
|---|---|---|---|
| streaming | 2 | 2026-03-20 | No |
| validation | 1 | 2026-02-15 | No |
| backends | 0 | — | Yes |

## Cross-Reference: Publications vs Mentions
- The streaming blog post appeared in 3 organic mentions on Reddit
- "backends" is mentioned frequently but has no published asset

## Recommendations
1. Write a demo showcasing backend switching (backends has zero coverage)
2. Create a social post about streaming validation (high mention overlap)
3. Refresh the social_post pipeline — only one post in two months
"""


def test_skill_manifest():
    from agents.monitor.publications import SKILL_MANIFEST

    assert "monitor/publications-tracking" in SKILL_MANIFEST["always"]
    assert SKILL_MANIFEST["post_processing"] == []


def test_report_generation(tmp_path):
    with patch("agents.monitor.publications._get_tracked_assets") as mock_assets, \
         patch("agents.monitor.publications._load_mention_data") as mock_mentions, \
         patch("agents.monitor.publications.LLMClient") as MockLLM, \
         patch("agents.monitor.publications.save_brief") as mock_brief, \
         patch("agents.monitor.publications.save_draft") as mock_save:

        mock_assets.return_value = [
            {"title": "Streaming Blog", "type": "blog", "number": 1},
            {"title": "Demo Video", "type": "demo", "number": 2},
        ]
        mock_mentions.return_value = {"weekly-report": {"mentions": 5}}
        MockLLM.return_value.generate_with_template.return_value = SAMPLE_REPORT
        mock_save.return_value = DraftOutput(
            agent_name="monitor-publications",
            content=SAMPLE_REPORT,
            file_path=str(tmp_path / "report.md"),
            metadata={"asset_count": 2, "type_breakdown": {"blog": 1, "demo": 1}},
        )

        from agents.monitor.publications import run
        output = run()

    assert output.agent_name == "monitor-publications"
    MockLLM.return_value.generate_with_template.assert_called_once()
    mock_brief.assert_called_once()
    brief_data = mock_brief.call_args[0][1]
    assert brief_data["asset_count"] == 2


def test_no_tracked_assets(tmp_path):
    with patch("agents.monitor.publications._get_tracked_assets") as mock_assets, \
         patch("agents.monitor.publications._load_mention_data") as mock_mentions, \
         patch("agents.monitor.publications.LLMClient") as MockLLM, \
         patch("agents.monitor.publications.save_brief"), \
         patch("agents.monitor.publications.save_draft") as mock_save:

        mock_assets.return_value = []
        mock_mentions.return_value = {}
        MockLLM.return_value.generate_with_template.return_value = "# No assets tracked yet."
        mock_save.return_value = DraftOutput(
            agent_name="monitor-publications",
            content="# No assets tracked yet.",
            file_path=str(tmp_path / "report.md"),
            metadata={"asset_count": 0, "type_breakdown": {}},
        )

        from agents.monitor.publications import run
        output = run()

    assert output.content == "# No assets tracked yet."
    call_kwargs = MockLLM.return_value.generate_with_template.call_args
    template_vars = call_kwargs[0][1]
    assert template_vars["asset_count"] == 0


def test_source_filter(tmp_path):
    with patch("agents.monitor.publications._get_tracked_assets") as mock_assets, \
         patch("agents.monitor.publications._load_mention_data") as mock_mentions, \
         patch("agents.monitor.publications.LLMClient") as MockLLM, \
         patch("agents.monitor.publications.save_brief"), \
         patch("agents.monitor.publications.save_draft") as mock_save:

        mock_assets.return_value = [
            {"title": "Blog A", "type": "blog", "number": 1},
            {"title": "Demo B", "type": "demo", "number": 2},
        ]
        mock_mentions.return_value = {}
        MockLLM.return_value.generate_with_template.return_value = SAMPLE_REPORT
        mock_save.return_value = DraftOutput(
            agent_name="monitor-publications",
            content=SAMPLE_REPORT,
            file_path=str(tmp_path / "report.md"),
            metadata={"asset_count": 1, "type_breakdown": {"blog": 1}},
        )

        from agents.monitor.publications import run
        run(sources=["blog"])

    template_vars = MockLLM.return_value.generate_with_template.call_args[0][1]
    assert template_vars["asset_count"] == 1


def test_saves_brief(tmp_path):
    with patch("agents.monitor.publications._get_tracked_assets") as mock_assets, \
         patch("agents.monitor.publications._load_mention_data") as mock_mentions, \
         patch("agents.monitor.publications.LLMClient") as MockLLM, \
         patch("agents.monitor.publications.save_brief") as mock_brief, \
         patch("agents.monitor.publications.save_draft") as mock_save:

        mock_assets.return_value = [{"title": "X", "type": "blog", "number": 1}]
        mock_mentions.return_value = {}
        MockLLM.return_value.generate_with_template.return_value = SAMPLE_REPORT
        mock_save.return_value = DraftOutput(
            agent_name="monitor-publications",
            content=SAMPLE_REPORT,
            file_path=str(tmp_path / "report.md"),
            metadata={},
        )

        from agents.monitor.publications import run
        run()

    mock_brief.assert_called_once_with("publications", mock_brief.call_args[0][1])
    brief_data = mock_brief.call_args[0][1]
    assert "generated_at" in brief_data
    assert brief_data["asset_count"] == 1

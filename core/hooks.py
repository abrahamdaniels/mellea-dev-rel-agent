"""Post-hook system for fire-and-forget side effects after agent runs."""

from __future__ import annotations

import logging

logger = logging.getLogger("hooks")

POST_HOOKS: dict[str, list[str]] = {
    "demo.packager": [
        "tracker.log_asset",
    ],
}


def run_post_hooks(agent_name: str, agent_output: dict) -> None:
    """Run post-hooks for the named agent. Best-effort: failures are logged."""
    for pattern, hooks in POST_HOOKS.items():
        if _matches(agent_name, pattern):
            for hook in hooks:
                try:
                    _invoke_hook(hook, agent_output)
                except Exception as exc:
                    logger.warning("Post-hook %s failed: %s", hook, exc)


def _matches(agent_name: str, pattern: str) -> bool:
    """Check if agent_name matches a hook pattern.

    Supports exact match and prefix match with dot notation.
    """
    return agent_name == pattern or agent_name.startswith(pattern + ".")


def _invoke_hook(hook: str, context: dict) -> None:
    """Resolve and invoke a hook by its dotted name."""
    if hook == "tracker.log_asset":
        from agents.tracker.log_asset import run

        path = context.get("path", "")
        if path:
            run(
                context_inputs=[path],
                asset_type="demo",
                dry_run=False,
            )
        else:
            logger.warning(
                "tracker.log_asset hook: no path in agent output"
            )
    else:
        raise ValueError(f"Unknown hook: {hook}")

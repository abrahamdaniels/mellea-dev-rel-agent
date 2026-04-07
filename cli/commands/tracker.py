from __future__ import annotations

from typing import Annotated, Optional

import typer

app = typer.Typer(help="Asset tracking commands")


@app.command()
def log(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="URL to published asset or description text.",
        ),
    ] = [],
    asset_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="Override asset type (blog, demo, talk, etc.)."),
    ] = None,
    title: Annotated[
        Optional[str],
        typer.Option("--title", help="Override asset title."),
    ] = None,
    link: Annotated[
        Optional[str],
        typer.Option("--link", help="Override asset URL."),
    ] = None,
    feature: Annotated[
        Optional[str],
        typer.Option("--feature", help="Override Mellea feature."),
    ] = None,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print issue body without creating."),
    ] = False,
) -> None:
    """Log a published asset to the GitHub project board."""
    from agents.tracker.log_asset import run

    result = run(
        context_inputs=list(context),
        asset_type=asset_type,
        title=title,
        link=link,
        feature=feature,
        no_cache=no_cache,
        dry_run=dry_run,
    )

    if result.get("issue_number"):
        typer.echo(f"Logged as issue #{result['issue_number']}")
    elif dry_run:
        typer.echo("Dry run complete.")


@app.command()
def sync(
    source: Annotated[
        list[str],
        typer.Option(
            "--source",
            "-s",
            help="Platforms to scan (default: all configured).",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print report to stdout only."),
    ] = True,
) -> None:
    """Scan for untracked assets and report gaps."""
    from agents.tracker.sync import run

    result = run(
        scan_platforms=list(source) if source else None,
        stdout_only=stdout_only,
    )

    untracked_count = len(result.get("untracked", []))
    if untracked_count:
        typer.echo(f"\n{untracked_count} untracked asset(s) found.")
    else:
        typer.echo("\nAll assets tracked.")

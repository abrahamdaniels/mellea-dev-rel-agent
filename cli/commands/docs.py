from __future__ import annotations

from typing import Annotated, Optional

import typer

app = typer.Typer(help="Documentation management commands")


@app.command()
def update(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="PR URL, changelog, feature spec, or free text.",
        ),
    ] = [],
    scope: Annotated[
        Optional[str],
        typer.Option("--scope", "-s", help="Target docs directory or file path."),
    ] = None,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print changes without creating PR."),
    ] = False,
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print to stdout only."),
    ] = False,
) -> None:
    """Generate documentation updates from context and create a PR."""
    from agents.docs.writer import run

    result = run(
        context_inputs=list(context),
        scope=scope,
        no_cache=no_cache,
        dry_run=dry_run,
        stdout_only=stdout_only,
    )

    pr_num = result.get("pr_number")
    if pr_num:
        typer.echo(f"Documentation PR #{pr_num} created.")
    elif dry_run or stdout_only:
        typer.echo("Dry run complete.")


@app.command()
def review(
    scope: Annotated[
        Optional[str],
        typer.Option("--scope", "-s", help="Docs directory or file to review."),
    ] = None,
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="API source code for accuracy cross-checking (optional).",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only/--save", help="Print to stdout (default) or save."),
    ] = True,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache."),
    ] = False,
    create_issues: Annotated[
        bool,
        typer.Option("--create-issues", help="Create GitHub issues for critical findings."),
    ] = False,
) -> None:
    """Review documentation quality and LLM-readability."""
    from agents.docs.reviewer import run

    result = run(
        scope=scope,
        context_inputs=list(context) if context else None,
        no_cache=no_cache,
        stdout_only=stdout_only,
        create_issues=create_issues,
    )

    findings_count = len(result.get("findings", []))
    if findings_count:
        typer.echo(f"\n{findings_count} finding(s) reported.")
    else:
        typer.echo("\nNo findings.")

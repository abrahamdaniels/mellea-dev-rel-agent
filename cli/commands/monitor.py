from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(help="Adoption monitoring agents")


@app.command()
def report(
    source: Annotated[
        list[str], typer.Option("--source", "-s", help="Filter mention sources (repeatable)")
    ] = [],
    stdout_only: Annotated[
        bool, typer.Option("--stdout-only", help="Print to stdout only, skip file write")
    ] = False,
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="Skip mention/stats cache")
    ] = False,
) -> None:
    """Generate a weekly monitor report."""
    from agents.monitor.report import run

    run(
        sources=source if source else None,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )


@app.command()
def mentions(
    source: Annotated[
        list[str], typer.Option("--source", "-s", help="Filter mention sources (repeatable)")
    ] = [],
    stdout_only: Annotated[
        bool, typer.Option("--stdout-only/--save", help="Print to stdout (default) or save to file")
    ] = True,
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="Skip cache")
    ] = False,
) -> None:
    """Check recent mentions across platforms."""
    from agents.monitor.mentions import run

    run(
        sources=source if source else None,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )


@app.command()
def publications(
    source: Annotated[
        list[str], typer.Option("--source", "-s", help="Filter by asset type (repeatable)")
    ] = [],
    stdout_only: Annotated[
        bool, typer.Option("--stdout-only", help="Print to stdout only, skip file write")
    ] = False,
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="Skip cache")
    ] = False,
) -> None:
    """Generate a publications performance report."""
    from agents.monitor.publications import run

    run(
        sources=source if source else None,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )

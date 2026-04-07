from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(help="Content creation agents")


@app.command()
def social(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Repeatable context: GitHub URL, file path, or free text.",
        ),
    ] = [],
    tone: Annotated[
        str,
        typer.Option("--tone", "-t", help="Tone: personal or ibm"),
    ] = "personal",
    platform: Annotated[
        str,
        typer.Option("--platform", "-p", help="Platform: twitter, linkedin, or both"),
    ] = "both",
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print to stdout only, skip saving to file"),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache"),
    ] = False,
) -> None:
    """Generate social media post drafts."""
    from agents.content.social_post import run

    if tone not in ("personal", "ibm"):
        typer.echo(f"Error: --tone must be 'personal' or 'ibm', got {tone!r}", err=True)
        raise typer.Exit(1)
    if platform not in ("twitter", "linkedin", "both"):
        typer.echo(
            f"Error: --platform must be 'twitter', 'linkedin', or 'both', got {platform!r}",
            err=True,
        )
        raise typer.Exit(1)

    run(
        context_inputs=list(context),
        tone=tone,
        platform=platform,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )


@app.command(name="technical-blog")
def technical_blog(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Repeatable context: GitHub URL, file path, or free text.",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print to stdout only, skip saving to file"),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache"),
    ] = False,
) -> None:
    """Generate a HuggingFace-style technical blog post."""
    from agents.content.technical_blog import run

    run(
        context_inputs=list(context),
        stdout_only=stdout_only,
        no_cache=no_cache,
    )


@app.command()
def suggest(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Additional context inputs (optional, briefs loaded automatically).",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only/--save", help="Print to stdout (default) or save to file"),
    ] = True,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache"),
    ] = False,
) -> None:
    """Suggest content topics based on monitor data."""
    from agents.content.suggest import run

    run(
        context_inputs=list(context) if context else None,
        stdout_only=stdout_only,
        no_cache=no_cache,
    )


@app.command(name="blog-outline")
def blog_outline(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Repeatable context: GitHub URL, file path, or free text.",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print to stdout only, skip saving to file"),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache"),
    ] = False,
) -> None:
    """Generate a blog post outline (headers + bullets, not prose)."""
    from agents.content.blog_outline import run

    run(
        context_inputs=list(context),
        stdout_only=stdout_only,
        no_cache=no_cache,
    )


@app.command(name="personal-blog")
def personal_blog(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Repeatable context: GitHub URL, file path, or free text.",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print to stdout only, skip saving to file"),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Skip context cache"),
    ] = False,
) -> None:
    """Generate a conversational personal blog post."""
    from agents.content.personal_blog import run

    run(
        context_inputs=list(context),
        stdout_only=stdout_only,
        no_cache=no_cache,
    )

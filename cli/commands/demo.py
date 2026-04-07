from __future__ import annotations

from typing import Annotated, Optional

import typer

app = typer.Typer(help="Demo pipeline commands")


@app.command()
def ideate(
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Feature description, PR URL, or free text.",
        ),
    ] = [],
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print to stdout only, skip saving to file"),
    ] = False,
) -> None:
    """Generate demo concepts from context."""
    from agents.demo.ideation import run

    run(
        context_inputs=list(context) if context else None,
        stdout_only=stdout_only,
    )


@app.command(name="run")
def run_pipeline(
    concept: Annotated[
        str,
        typer.Argument(help="Concept text, file path, or path:N selector."),
    ],
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Additional context for code generation.",
        ),
    ] = [],
    output_dir: Annotated[
        Optional[str],
        typer.Option("--output-dir", "-o", help="Override output directory."),
    ] = None,
) -> None:
    """Run the full demo pipeline: generate -> test -> package."""
    from agents.demo.pipeline import run

    results = run(
        concept=concept,
        context_inputs=list(context) if context else None,
        output_dir=output_dir,
    )

    # Print summary
    for r in results:
        status = "PASS" if r.success else "FAIL"
        typer.echo(f"  [{status}] {r.stage_name}")
        if r.error_context:
            typer.echo(f"         {r.error_context[:200]}")

    if results and not results[-1].success:
        raise typer.Exit(1)


@app.command()
def generate(
    concept: Annotated[
        str,
        typer.Argument(help="Concept text, file path, or path:N selector."),
    ],
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            "-c",
            help="Additional context.",
        ),
    ] = [],
    output_dir: Annotated[
        Optional[str],
        typer.Option("--output-dir", "-o", help="Override output directory."),
    ] = None,
) -> None:
    """Generate demo code from a concept (standalone, no pipeline)."""
    from agents.demo.code_gen import run

    result = run(
        concept=concept,
        context_inputs=list(context) if context else None,
        output_dir=output_dir,
    )
    if result.success:
        typer.echo(f"Generated files in {result.output.get('path', 'unknown')}")
    else:
        typer.echo(f"Generation failed: {result.error_context}", err=True)
        raise typer.Exit(1)


@app.command()
def test(
    path: Annotated[
        str,
        typer.Argument(help="Path to demo directory."),
    ],
    timeout: Annotated[
        Optional[int],
        typer.Option("--timeout", help="Test timeout in seconds."),
    ] = None,
) -> None:
    """Run tests on a generated demo."""
    from agents.demo.test_runner import run

    result = run(path=path, timeout=timeout)
    test_result = result.output.get("test_result")

    if test_result:
        typer.echo(
            f"Tests: {test_result.total_tests} total, "
            f"{test_result.failed_tests} failed"
        )

    if result.success:
        typer.echo("All tests passed.")
    else:
        typer.echo(f"Tests failed: {result.error_context}", err=True)
        raise typer.Exit(1)


@app.command()
def package(
    path: Annotated[
        str,
        typer.Argument(help="Path to demo directory."),
    ],
    concept: Annotated[
        Optional[str],
        typer.Option("--concept", help="Concept description for README context."),
    ] = None,
    stdout_only: Annotated[
        bool,
        typer.Option("--stdout-only", help="Print README to stdout instead of writing."),
    ] = False,
    no_hooks: Annotated[
        bool,
        typer.Option("--no-hooks", help="Skip post-hooks (e.g. asset tracking)."),
    ] = False,
) -> None:
    """Package a demo with README and polish."""
    from agents.demo.packager import run

    result = run(path=path, concept=concept, stdout_only=stdout_only, no_hooks=no_hooks)
    if result.success:
        typer.echo(f"Packaged demo at {result.output.get('path', 'unknown')}")
    else:
        typer.echo(f"Packaging failed: {result.error_context}", err=True)
        raise typer.Exit(1)

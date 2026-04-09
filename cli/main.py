from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import typer

from cli.commands import content, demo, docs, monitor, tracker

app = typer.Typer(
    name="devrel",
    help="Mellea DevRel Agent System — content creation, monitoring, demos, and docs.",
    no_args_is_help=True,
)

app.add_typer(content.app, name="content")
app.add_typer(monitor.app, name="monitor")
app.add_typer(demo.app, name="demo")
app.add_typer(tracker.app, name="tracker")
app.add_typer(docs.app, name="docs")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

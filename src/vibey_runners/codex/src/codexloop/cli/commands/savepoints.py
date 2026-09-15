# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop savepoints`` — list git save points for a run."""

from __future__ import annotations

import typer

from codexloop.bootstrap import list_savepoints
from codexloop.domain.errors import ConfigurationError


def savepoints(
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """List numbered git save points."""
    try:
        points = list_savepoints(run_id=run_id)
    except ConfigurationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    if not points:
        typer.echo("no savepoints")
        return
    for point in points:
        committed = "commit" if point.committed else "ref-only"
        typer.echo(f"{point.n}\t{point.sha[:12]}\t{committed}\t{point.label}\t{point.ref}")

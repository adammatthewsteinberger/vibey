# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop reset`` — create a labeled savepoint of the current tree."""

from __future__ import annotations

import typer

from codexloop.bootstrap import create_savepoint
from codexloop.domain.errors import ConfigurationError


def reset(
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
    label: str = typer.Option("reset", "--label", help="Savepoint label."),
) -> None:
    """Record a savepoint (commit if dirty, else ref-tag only)."""
    try:
        point = create_savepoint(label=label, run_id=run_id, summary="operator reset")
    except ConfigurationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    if point is None:
        typer.echo("not a git repository — no savepoint created")
        raise typer.Exit(1)
    kind = "commit" if point.committed else "ref-only"
    typer.echo(f"savepoint {point.n} ({kind}) {point.sha[:12]}")

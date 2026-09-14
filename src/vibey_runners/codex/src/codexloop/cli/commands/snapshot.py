# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop snapshot`` — copy the workspace excluding ``.codexloop/``."""

from __future__ import annotations

import typer

from codexloop.bootstrap import restore_run_snapshot, take_snapshot
from codexloop.domain.errors import ConfigurationError


def snapshot(
    name: str | None = typer.Argument(None, help="Snapshot name (default: timestamp)."),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
    restore: str | None = typer.Option(None, "--restore", help="Restore a named snapshot."),
) -> None:
    """Create or restore a filesystem snapshot for the active run."""
    try:
        if restore is not None:
            restore_run_snapshot(restore, run_id=run_id)
            typer.echo(f"restored snapshot {restore}")
            return
        path = take_snapshot(run_id=run_id, name=name)
    except (ConfigurationError, FileNotFoundError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"snapshot → {path}")

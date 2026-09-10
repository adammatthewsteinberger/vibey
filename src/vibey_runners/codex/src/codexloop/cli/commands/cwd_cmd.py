# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop cwd`` — enqueue SetCwd."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.control import SetCwd
from codexloop.domain.errors import ConfigurationError


def cwd_cmd(
    path: str = typer.Argument(..., help="Working directory path."),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """Queue a cwd change for the next control boundary."""
    try:
        written = enqueue_run_control(SetCwd(cwd=path), run_id=run_id)
    except ConfigurationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued → {written}")

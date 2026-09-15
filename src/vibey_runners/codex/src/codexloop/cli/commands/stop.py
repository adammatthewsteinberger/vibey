# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop stop`` — enqueue a Stop control command."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.control import Stop
from codexloop.domain.errors import ConfigurationError


def stop(
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """Request a graceful stop at the next control boundary."""
    try:
        path = enqueue_run_control(Stop(), run_id=run_id)
    except ConfigurationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued stop → {path}")

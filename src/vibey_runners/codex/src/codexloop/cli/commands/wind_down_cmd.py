# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop wind-down`` — enqueue a WindDownCommand control command."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.control import WindDownCommand
from codexloop.domain.errors import ConfigurationError


def wind_down(
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
    reason: str | None = typer.Option(
        None,
        "--reason",
        help="Reason for wind-down (e.g., 'capacity exhausted', 'smoke test').",
    ),
) -> None:
    """Request a graceful wind-down at the next control boundary.

    The run finishes the current turn, writes a handoff marker naming every
    artifact produced, and exits with code 75 so a supervisor can distinguish
    "hand this run off elsewhere" from "it failed" or "the operator hard-stopped it".
    """
    if reason is None:
        reason = "operator request"
    try:
        cmd = WindDownCommand(reason=reason)
        path = enqueue_run_control(cmd, run_id=run_id)
    except (ConfigurationError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued wind-down → {path}")

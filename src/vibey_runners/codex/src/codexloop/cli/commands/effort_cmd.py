# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop effort`` — enqueue SetEffort."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.control import SetEffort
from codexloop.domain.errors import ConfigurationError
from codexloop.domain.model_profile import Effort


def effort_cmd(
    effort: str = typer.Argument(..., help="Effort level."),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """Queue an effort change for the next control boundary."""
    try:
        value = Effort(effort)
        path = enqueue_run_control(SetEffort(effort=value), run_id=run_id)
    except (ConfigurationError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued → {path}")

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop model`` — enqueue SetModel."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.control import SetModel
from codexloop.domain.errors import ConfigurationError


def model_cmd(
    model: str = typer.Argument(..., help="Model name."),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """Queue a model change for the next control boundary."""
    try:
        path = enqueue_run_control(SetModel(model=model), run_id=run_id)
    except ConfigurationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued → {path}")

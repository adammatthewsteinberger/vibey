# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def model_cmd(
    model: str = typer.Argument(..., help="Alias (low|medium|high) or raw Anthropic model id"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Queue a mid-run model change at the next turn boundary."""
    try:
        result = bootstrap_ops.enqueue_model(Path.cwd(), model, run_id=run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued set_model for run {result.run_id}: {model}")

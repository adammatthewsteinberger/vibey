# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def slash_cmd(
    text: str = typer.Argument(..., help="Slash command text (must start with /)"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Inject a validated slash command into an active loop session."""
    if not text.startswith("/"):
        typer.echo("Slash command must start with '/'", err=True)
        raise typer.Exit(code=2)
    try:
        result = bootstrap_ops.enqueue_slash(Path.cwd(), text, run_id=run_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Enqueued slash for run {result.run_id}")

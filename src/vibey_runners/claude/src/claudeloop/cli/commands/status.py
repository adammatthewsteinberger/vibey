# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def status(
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(
        None,
        "--cwd",
        exists=True,
        file_okay=False,
        help="Effective working directory (default: current directory)",
    ),
) -> None:
    """Show status for the active (or specified) run."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        info = bootstrap_ops.run_status(cwd, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    for key, value in info.items():
        typer.echo(f"{key}: {value}")

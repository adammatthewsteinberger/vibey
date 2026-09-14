# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def preset_cmd(
    preset: str = typer.Argument(..., help="Preset name: low|medium|high"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Queue a mid-run preset (model+effort) change at the next turn boundary."""
    try:
        result = bootstrap_ops.enqueue_preset(Path.cwd(), preset, run_id=run_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued set_preset for run {result.run_id}: {preset}")

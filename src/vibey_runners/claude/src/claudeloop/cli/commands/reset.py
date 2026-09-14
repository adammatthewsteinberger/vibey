# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Wipe the local `.claudeloop/` control plane for a project."""

from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def reset(
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Required confirmation — deletes the entire project .claudeloop/ tree",
    ),
) -> None:
    """Delete `.claudeloop/` (runs, state, locks). Refuses if a run is live."""
    cwd = Path.cwd()
    try:
        result = bootstrap_ops.reset_project_state(cwd, yes=yes)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Removed {result['path']}")

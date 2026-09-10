# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Wipe the local `.agyloop/` control plane for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def reset(
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            help="Required confirmation — deletes the entire project .agyloop/ tree",
        ),
    ] = False,
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
) -> None:
    """Delete `.agyloop/` (runs, state, locks). Refuses if a run is live."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = bootstrap.reset_project_state(cwd, yes=yes)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Removed {result['path']}")

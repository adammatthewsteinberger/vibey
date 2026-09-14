# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def status(
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
) -> None:
    """Show status for the active (or specified) run."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        info = bootstrap.run_status(cwd, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    for key, value in info.items():
        typer.echo(f"{key}: {value}")

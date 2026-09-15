# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def stop(
    cwd_dir: Annotated[
        Path | None,
        typer.Option(
            "--cwd",
            exists=True,
            file_okay=False,
            help="Working directory whose .agyloop/runs registry to target.",
        ),
    ] = None,
    run_id: Annotated[str | None, typer.Option("--run-id", help="Target run id.")] = None,
) -> None:
    """Request a soft stop of the active (or specified) run.

    The runner finishes the current turn or aborts a wait, writes a stop
    summary, and exits.
    """
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = bootstrap.enqueue_stop(cwd, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Stop requested for run {result.run_id}")

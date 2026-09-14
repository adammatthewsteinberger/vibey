# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def preset_cmd(
    preset: Annotated[str, typer.Argument(help="Preset name: low|medium|high")],
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
) -> None:
    """Queue a mid-run preset (model+effort) change at the next turn boundary."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = bootstrap.enqueue_preset(cwd, preset, run_id=run_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued set_preset for run {result.run_id}: {preset}")

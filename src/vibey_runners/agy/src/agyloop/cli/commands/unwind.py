# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def unwind(
    to: Annotated[str, typer.Option("--to", help="Save point number, sha prefix, or label")],
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    backup: Annotated[
        bool,
        typer.Option("--backup/--no-backup", help="Create a backup ref before resetting"),
    ] = True,
    cwd_dir: Annotated[
        Path | None,
        typer.Option("--cwd", exists=True, file_okay=False),
    ] = None,
) -> None:
    """Unwind the worktree to a prior save point (refuses while a run is active)."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = bootstrap.unwind_savepoint(cwd, to, backup=backup, run_id=run_id)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Restored save point #{result['to_n']} ({result['restored_sha'][:12]})")
    if result["backup_ref"]:
        typer.echo(f"Backup ref: {result['backup_ref']}")

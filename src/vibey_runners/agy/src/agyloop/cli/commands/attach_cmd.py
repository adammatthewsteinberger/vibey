# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def attach(
    path: Annotated[Path, typer.Argument(exists=True, help="File or directory to attach")],
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
) -> None:
    """Attach a file or directory to the active run."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = bootstrap.enqueue_resource(
            cwd,
            action="add",
            kind="attachment",
            value=str(path.resolve()),
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued attach for run {result.run_id}: {path}")


def unattach(
    name: Annotated[str, typer.Argument(help="Attachment name (basename) to remove")],
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
) -> None:
    """Remove an attachment from the active run."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = bootstrap.enqueue_resource(
            cwd,
            action="rm",
            kind="attachment",
            value=name,
            name=name,
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued unattach for run {result.run_id}: {name}")

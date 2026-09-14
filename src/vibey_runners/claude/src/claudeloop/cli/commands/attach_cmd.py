# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def attach(
    path: Path = typer.Argument(..., exists=True, help="File or directory to attach"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Attach a file or directory to the active run."""
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
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
    name: str = typer.Argument(..., help="Attachment name (basename) to remove"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Remove an attachment from the active run."""
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
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

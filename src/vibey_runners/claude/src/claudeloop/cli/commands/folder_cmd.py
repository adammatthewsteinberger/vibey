# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Add or remove extra workspace folders for the active run")


@app.command("add")
def add(
    path: Path = typer.Argument(..., exists=True, file_okay=False, help="Folder to add"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
            action="add",
            kind="folder",
            value=str(path.resolve()),
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued folder add for run {result.run_id}: {path}")


@app.command("rm")
def rm(
    path: Path = typer.Argument(..., help="Folder path to remove"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
            action="rm",
            kind="folder",
            value=str(path),
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued folder rm for run {result.run_id}: {path}")

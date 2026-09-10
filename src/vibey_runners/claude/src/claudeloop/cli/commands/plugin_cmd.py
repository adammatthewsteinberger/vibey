# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Add or remove plugins for the active run")


@app.command("add")
def add(
    name: str = typer.Argument(..., help="Plugin name"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(), action="add", kind="plugin", value=name, run_id=run_id
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued plugin add for run {result.run_id}: {name}")


@app.command("rm")
def rm(
    name: str = typer.Argument(..., help="Plugin name"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(), action="rm", kind="plugin", value=name, run_id=run_id
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued plugin rm for run {result.run_id}: {name}")

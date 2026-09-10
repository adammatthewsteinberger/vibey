# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Deep research sessions for the active run")


@app.command("start")
def start(
    query: str = typer.Argument(..., help="Research query"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
            action="add",
            kind="research",
            value=query,
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued research start for run {result.run_id}")


@app.command("status")
def status(
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        rows = bootstrap_ops.research_status(Path.cwd(), run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if not rows:
        typer.echo("No research sessions.")
        return
    for row in rows:
        typer.echo(json.dumps(row))

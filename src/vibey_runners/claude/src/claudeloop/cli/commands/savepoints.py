# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="List git save points for a run")


@app.callback(invoke_without_command=True)
def savepoints(
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    cwd = Path.cwd()
    try:
        points = bootstrap_ops.list_savepoints(cwd, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if not points:
        typer.echo("No save points.")
        return
    for point in points:
        typer.echo(
            f"#{point['n']}  {point['sha'][:12]}  {point['label']}  {point['at']}  {point['ref']}"
        )

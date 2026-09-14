# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Run-scoped memory notes")


@app.command("list")
def list_cmd(
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        items = bootstrap_ops.memory_list(Path.cwd(), run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if not items:
        typer.echo("No memories.")
        return
    for item in items:
        typer.echo(item.get("name", ""))


@app.command("get")
def get(
    name: str = typer.Argument(..., help="Memory name"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        body = bootstrap_ops.memory_get(Path.cwd(), name, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(body)


@app.command("set")
def set_cmd(
    name: str = typer.Argument(..., help="Memory name"),
    body: str = typer.Argument(..., help="Memory body text"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        path = bootstrap_ops.memory_set(Path.cwd(), name, body, run_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Wrote memory {name} → {path}")


@app.command("rm")
def rm(
    name: str = typer.Argument(..., help="Memory name"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        bootstrap_ops.memory_rm(Path.cwd(), name, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Removed memory {name}")

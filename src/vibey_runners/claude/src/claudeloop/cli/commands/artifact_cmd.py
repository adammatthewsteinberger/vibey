# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Run-scoped artifact files")


@app.command("list")
def list_cmd(
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        names = bootstrap_ops.artifact_list(Path.cwd(), run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if not names:
        typer.echo("No artifacts.")
        return
    for name in names:
        typer.echo(name)


@app.command("get")
def get(
    name: str = typer.Argument(..., help="Artifact name"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        path = bootstrap_ops.artifact_get(Path.cwd(), name, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(path.read_text(encoding="utf-8"))


@app.command("put")
def put(
    name: str = typer.Argument(..., help="Artifact name"),
    source: Path = typer.Argument(..., exists=True, help="Source file"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        dest = bootstrap_ops.artifact_put(Path.cwd(), name, source, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Stored artifact {name} → {dest}")


@app.command("rm")
def rm(
    name: str = typer.Argument(..., help="Artifact name"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        bootstrap_ops.artifact_rm(Path.cwd(), name, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Removed artifact {name}")

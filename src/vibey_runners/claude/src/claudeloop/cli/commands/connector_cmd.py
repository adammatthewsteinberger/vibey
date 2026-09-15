# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Manage MCP connectors for the active run")


@app.command("add")
def add(
    name: str = typer.Argument(..., help="Connector name"),
    config: str = typer.Argument(..., help="JSON config or http(s) URL"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    value = config.strip()
    if value.startswith("{"):
        try:
            json.loads(value)
        except json.JSONDecodeError as exc:
            typer.echo(f"Invalid connector JSON: {exc}", err=True)
            raise typer.Exit(code=2) from exc
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
            action="add",
            kind="connector",
            value=value,
            name=name,
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued connector add for run {result.run_id}: {name}")


@app.command("rm")
def rm(
    name: str = typer.Argument(..., help="Connector name"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
            action="rm",
            kind="connector",
            value=name,
            name=name,
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued connector rm for run {result.run_id}: {name}")


@app.command("list")
def list_cmd(
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        store = bootstrap_ops.get_resource_store(Path.cwd(), run_id)
        connectors = store.list_connectors()
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if not connectors:
        typer.echo("No connectors.")
        return
    for key, cfg in sorted(connectors.items()):
        typer.echo(f"{key}: {json.dumps(cfg)}")

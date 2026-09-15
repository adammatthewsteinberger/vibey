# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Approve or deny pending tool uses (manual permission mode)")


@app.command("approve")
def approve(
    request_id: str = typer.Argument(..., help="Pending tool request id"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Approve a pending tool use."""
    try:
        result = bootstrap_ops.enqueue_tool_decision(
            Path.cwd(), request_id, allow=True, run_id=run_id
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Approved tool {request_id} for run {result.run_id}")


@app.command("deny")
def deny(
    request_id: str = typer.Argument(..., help="Pending tool request id"),
    reason: str = typer.Option("", "--reason", help="Denial reason shown to the agent"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Deny a pending tool use."""
    try:
        result = bootstrap_ops.enqueue_tool_decision(
            Path.cwd(), request_id, allow=False, reason=reason, run_id=run_id
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Denied tool {request_id} for run {result.run_id}")

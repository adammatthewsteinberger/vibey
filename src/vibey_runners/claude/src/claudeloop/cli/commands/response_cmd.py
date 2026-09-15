# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Feedback and retry for the last assistant response")


@app.command("copy")
def copy(
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        text = bootstrap_ops.copy_response(Path.cwd(), run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if not text:
        typer.echo("No assistant response found.", err=True)
        raise typer.Exit(code=1)
    typer.echo(text)


@app.command("good")
def good(
    note: str = typer.Option("", "--note", help="Optional feedback note"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_response_feedback(
            Path.cwd(), "good", note=note, run_id=run_id
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued good feedback for run {result.run_id}")


@app.command("bad")
def bad(
    note: str = typer.Option("", "--note", help="Optional feedback note"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_response_feedback(
            Path.cwd(), "bad", note=note, run_id=run_id
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued bad feedback for run {result.run_id}")


@app.command("retry")
def retry(
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_response_retry(Path.cwd(), run_id=run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued response retry for run {result.run_id}")

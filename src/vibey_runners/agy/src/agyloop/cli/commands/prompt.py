# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def prompt(
    text: Annotated[str, typer.Argument(help="Prompt text to inject into the loop.")],
    now: Annotated[
        bool,
        typer.Option("--now", help="Apply at the next operator boundary (immediate)."),
    ] = False,
    at_break: Annotated[
        bool,
        typer.Option(
            "--at-break",
            help="Apply only at a natural break (after Continue, before next send).",
        ),
    ] = False,
    cwd_dir: Annotated[
        Path | None,
        typer.Option(
            "--cwd",
            exists=True,
            file_okay=False,
            help="Working directory whose .agyloop/runs registry to target.",
        ),
    ] = None,
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
) -> None:
    """Inject a new prompt into an active loop session."""
    if now == at_break:
        typer.echo("Specify exactly one of --now or --at-break", err=True)
        raise typer.Exit(code=2)
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = bootstrap.enqueue_prompt(cwd, text, immediate=now, run_id=run_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Enqueued {result.command_type} for run {result.run_id}")

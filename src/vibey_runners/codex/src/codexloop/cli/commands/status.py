# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop status [run-id]``."""

from __future__ import annotations

import typer

from codexloop.bootstrap import read_run_record
from codexloop.cli.render import render_status


def status(
    run_id: str | None = typer.Argument(None, help="Run id. Defaults to the latest run."),
) -> None:
    """Show persisted state for a run."""
    typer.echo(render_status(read_run_record(run_id)))

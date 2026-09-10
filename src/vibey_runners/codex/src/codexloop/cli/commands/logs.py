# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop logs [run-id]``."""

from __future__ import annotations

import typer

from codexloop.bootstrap import read_run_events
from codexloop.cli.render import render_logs


def logs(
    run_id: str | None = typer.Argument(None, help="Run id. Defaults to the latest run."),
) -> None:
    """Print events.jsonl for a run."""
    typer.echo(render_logs(read_run_events(run_id)))

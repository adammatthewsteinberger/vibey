# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop watch`` — print current run state (one-shot or continuous)."""

from __future__ import annotations

import json
import time

import typer

from codexloop.bootstrap import (
    events_path_for_run,
    read_run_state,
    run_is_live,
    run_stream_ui_for_events,
)


def watch(
    run_id: str | None = typer.Argument(None, help="Run id. Defaults to the latest run."),
    replay: bool = typer.Option(
        False,
        "--replay",
        help="Open the Textual stream UI against the run event log.",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Keep printing state whenever it changes until the run exits.",
    ),
    interval: float = typer.Option(
        1.0,
        "--interval",
        min=0.1,
        help="Poll interval in seconds when --follow is set.",
    ),
) -> None:
    """Show a snapshot of persisted run state."""
    if replay:
        run_stream_ui_for_events(events_path_for_run(run_id))
        return
    if follow:
        _follow(run_id, interval=interval)
        return
    state = read_run_state(run_id)
    if not state:
        typer.echo("no run state")
        raise typer.Exit(1)
    typer.echo(json.dumps(state, indent=2, default=str))


def _follow(run_id: str | None, *, interval: float) -> None:
    last: dict[str, object] | None = None
    saw_state = False
    while True:
        state = read_run_state(run_id)
        if state and state != last:
            typer.echo(json.dumps(state, indent=2, default=str))
            last = state
            saw_state = True
        if saw_state and not run_is_live(run_id):
            return
        if not saw_state and not state:
            typer.echo("no run state")
            raise typer.Exit(1)
        time.sleep(interval)

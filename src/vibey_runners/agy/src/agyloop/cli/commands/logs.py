# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def logs(
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Follow like tail -f")] = False,
    chatter: Annotated[
        bool,
        typer.Option("--chatter", help="Only show chatter.* events (includes trace_id/turn_id)"),
    ] = False,
) -> None:
    """Tail the per-run events.jsonl stream (redacted, realtime)."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        bootstrap.tail_events(cwd, run_id=run_id, follow=follow, chatter_only=chatter)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except KeyboardInterrupt:
        raise typer.Exit(code=0) from None

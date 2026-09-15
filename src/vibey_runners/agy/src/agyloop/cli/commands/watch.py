# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def watch(
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
    follow: Annotated[
        bool,
        typer.Option("--follow/--no-follow", "-f", help="Follow bus.jsonl like tail -f"),
    ] = True,
    stream: Annotated[
        bool, typer.Option("--stream", help="Full-screen Textual token stream (events.jsonl)")
    ] = False,
    replay: Annotated[
        bool, typer.Option("--replay", help="Replay historical chatter.delta stream from disk")
    ] = False,
    speed: Annotated[
        float, typer.Option("--speed", help="Replay speed (1.0=realtime; unused for live follow)")
    ] = 1.0,
) -> None:
    """Subscribe to run state-change publications, or attach a stream UI."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        if stream or replay:
            bootstrap.run_stream_ui(
                cwd,
                run_id=run_id,
                follow=follow and not replay,
                replay=replay,
                speed=speed,
            )
            return
        bootstrap.watch_bus(cwd, run_id=run_id, follow=follow)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except KeyboardInterrupt:
        raise typer.Exit(code=0) from None

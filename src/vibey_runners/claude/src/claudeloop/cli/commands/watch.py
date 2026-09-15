# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops
from claudeloop.infrastructure.rundir import resolve_run_directory
from claudeloop.infrastructure.stream_ui import dump_transcript, run_textual_app


def watch(
    run_id: str | None = typer.Option(None, "--run-id"),
    follow: bool = typer.Option(
        True, "--follow/--no-follow", "-f", help="Follow bus.jsonl like tail -f"
    ),
    stream: bool = typer.Option(
        False, "--stream", help="Full-screen Textual token stream (events.jsonl)"
    ),
    replay: bool = typer.Option(
        False, "--replay", help="Replay historical chatter.delta stream from disk"
    ),
    speed: float = typer.Option(
        1.0, "--speed", help="Replay speed (1.0=realtime pacing ticks; 0=as fast as possible)"
    ),
    cwd_dir: Path | None = typer.Option(
        None,
        "--cwd",
        exists=True,
        file_okay=False,
        help="Effective working directory (default: current directory)",
    ),
) -> None:
    """Subscribe to run state-change publications, or attach a stream UI.

    Other systems can also poll ``status.json`` or follow ``bus.jsonl`` directly
    without this CLI — this command is the human-friendly subscriber.
    """
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        if stream or replay:
            directory = resolve_run_directory(cwd, run_id)
            events = directory.events_path
            if replay and not sys_stdout_isatty():
                dump_transcript(events)
                return
            run_textual_app(
                events_path=events,
                follow=follow and not replay,
                replay=replay,
                speed=speed,
            )
            return
        bootstrap_ops.watch_bus(cwd, run_id=run_id, follow=follow)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except KeyboardInterrupt:  # pragma: no cover
        raise typer.Exit(code=0) from None


def sys_stdout_isatty() -> bool:
    import sys

    return bool(sys.stdout.isatty())

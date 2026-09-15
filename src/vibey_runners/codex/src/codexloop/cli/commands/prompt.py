# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop prompt`` — queue an operator prompt into the run inbox."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.control import Prompt, PromptTiming
from codexloop.domain.errors import ConfigurationError


def prompt(
    text: str = typer.Argument(..., help="Prompt text to queue."),
    now: bool = typer.Option(False, "--now", help="Apply at the next control poll."),
    next_turn: bool = typer.Option(
        False,
        "--next-turn",
        help="Apply before the next turn.",
    ),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """Queue an operator prompt. Requires exactly one of --now / --next-turn."""
    if now == next_turn:
        typer.echo("Specify exactly one of --now or --next-turn.", err=True)
        raise typer.Exit(2)
    timing = PromptTiming.NOW if now else PromptTiming.NEXT_TURN
    try:
        path = enqueue_run_control(Prompt(text=text, timing=timing), run_id=run_id)
    except ConfigurationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued → {path}")

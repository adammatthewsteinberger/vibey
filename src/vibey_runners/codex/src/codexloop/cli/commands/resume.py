# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop resume [<thread-id> | --last]``."""

from __future__ import annotations

import typer

from codexloop.application.usecases.resume_thread import resume_thread
from codexloop.application.usecases.run_plan import run_plan
from codexloop.bootstrap import build_runner
from codexloop.cli.asyncio import async_command
from codexloop.cli.render import render_result
from codexloop.domain.session import MostRecent


@async_command
async def resume(
    thread_id: str | None = typer.Argument(None, help="Thread id to resume."),
    last: bool = typer.Option(False, "--last", help="Resume the most recent thread."),
    transport: str = typer.Option(
        "exec",
        "--transport",
        help="Agent transport: exec or app-server.",
    ),
) -> object:
    """Resume by explicit thread id (default) or the most recent catalog entry."""
    if thread_id is None and not last:
        typer.echo("Specify a thread id or --last.", err=True)
        raise typer.Exit(2)
    if thread_id is not None and last:
        typer.echo("Specify a thread id or --last, not both.", err=True)
        raise typer.Exit(2)
    ctx = build_runner(transport=transport)
    if thread_id is not None:
        result = await resume_thread(ctx, thread_id)
    else:
        result = await run_plan(ctx, MostRecent(), "")
    typer.echo(render_result(result))
    return result

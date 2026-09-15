# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop run <plan.md>``."""

from __future__ import annotations

from pathlib import Path

import typer

from codexloop.application.usecases.run_plan import run_plan
from codexloop.bootstrap import build_runner, events_path_for_run, run_stream_ui_for_events
from codexloop.cli.asyncio import async_command
from codexloop.cli.render import render_result
from codexloop.domain.session import PlanFile


@async_command
async def run(
    plan: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Markdown work plan.",
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Name this run instead of generating an id (lets a supervisor attach mid-run).",
    ),
    transport: str = typer.Option(
        "exec",
        "--transport",
        help="Agent transport: exec or app-server.",
    ),
    model: str | None = typer.Option(None, "--model", help="Model name."),
    max_turns: int | None = typer.Option(None, "--max-turns", help="Turn budget."),
    max_wait: str | None = typer.Option(None, "--max-wait", help="Max wait duration."),
    network_access: bool | None = typer.Option(
        None,
        "--network-access/--no-network-access",
        help=(
            "Allow outbound command network access inside the workspace-write sandbox. "
            "This is not limited to localhost."
        ),
    ),
    stream_ui: bool = typer.Option(
        False,
        "--stream-ui",
        help="Open a Textual live view of the run event log after completion.",
    ),
) -> object:
    """Drive a new autonomous run from a markdown work plan."""
    flags: dict[str, object] = {
        "model": model,
        "max_turns": max_turns,
        "max_wait": max_wait,
        "network_access": network_access,
    }
    try:
        ctx = build_runner(transport=transport, flags=flags, run_id=run_id)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    text = plan.read_text(encoding="utf-8")
    result = await run_plan(ctx, PlanFile(str(plan)), text)
    typer.echo(render_result(result))
    if stream_ui:
        run_stream_ui_for_events(events_path_for_run())
    return result

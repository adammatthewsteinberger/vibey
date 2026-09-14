# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Thin CLI commands — parse flags, call use cases, render exit codes."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import typer

from cursorloop import bootstrap
from cursorloop.application.usecases.run_plan import parse_plan_file, run_from_plan_file
from cursorloop.cli.asyncio import async_command
from cursorloop.cli.render import exit_code_for
from cursorloop.domain.errors import PlanParseError
from cursorloop.infrastructure.config import load_config


def run(
    plan: Path = typer.Option(
        ...,
        "--plan",
        exists=True,
        readable=True,
        help="Markdown plan file to seed a fresh agent run",
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Name this run instead of generating an id (lets a supervisor attach mid-run)",
    ),
    cwd_dir: Path | None = typer.Option(
        None, "--cwd", exists=True, file_okay=False, help="Working directory"
    ),
    max_turns: int | None = typer.Option(None, "--max-turns"),
    max_dollars: float | None = typer.Option(None, "--max-dollars"),
    max_wait: float | None = typer.Option(None, "--max-wait", help="Max wait seconds"),
    turn_timeout: float | None = typer.Option(
        None, "--turn-timeout", help="Per-turn wall-clock timeout seconds"
    ),
    stall_timeout: float | None = typer.Option(
        None, "--stall-timeout", help="No-delta stall timeout seconds"
    ),
    managed_hooks: bool = typer.Option(
        True, "--managed-hooks/--no-managed-hooks", help="Merge autonomy hooks.json"
    ),
    model: str | None = typer.Option(None, "--model"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    """Seed a Cursor Agent from PLAN and run autonomously to completion."""
    _run(
        plan=plan,
        run_id=run_id,
        cwd_dir=cwd_dir,
        max_turns=max_turns,
        max_dollars=max_dollars,
        max_wait=max_wait,
        turn_timeout=turn_timeout,
        stall_timeout=stall_timeout,
        managed_hooks=managed_hooks,
        model=model,
        log_level=log_level,
    )


@async_command
async def _run(
    *,
    plan: Path,
    run_id: str | None,
    cwd_dir: Path | None,
    max_turns: int | None,
    max_dollars: float | None,
    max_wait: float | None,
    turn_timeout: float | None,
    stall_timeout: float | None,
    managed_hooks: bool,
    model: str | None,
    log_level: str,
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    config = load_config()
    overrides: dict[str, object] = {
        "max_turns": max_turns,
        "max_dollars": max_dollars,
        "max_wait_seconds": max_wait,
        "turn_timeout_seconds": turn_timeout,
        "stall_timeout_seconds": stall_timeout,
        "model": model,
        "log_level": log_level,
        "managed_hooks": managed_hooks,
    }
    cleaned = {k: v for k, v in overrides.items() if v is not None}
    config = replace(config, **cleaned)  # type: ignore[arg-type]

    try:
        parse_plan_file(plan)
    except (PlanParseError, ValueError, OSError) as exc:
        typer.echo(f"Invalid plan file: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        built = bootstrap.build_runner(cwd=cwd, config=config, plan_path=plan, run_id=run_id)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    except FileExistsError as exc:
        typer.echo(
            f"Run id {run_id!r} already exists; pick another or use `cursorloop resume`.",
            err=True,
        )
        raise typer.Exit(code=2) from exc
    except RuntimeError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    try:
        typer.echo(f"Run id: {built.run_id}", err=True)
        result = await run_from_plan_file(built.runner, plan)
    finally:
        built.close()
    if not result.success:
        typer.echo(f"Run failed: {result.reason}", err=True)
        raise typer.Exit(code=exit_code_for(result))
    typer.echo(f"Done: {result.reason}")

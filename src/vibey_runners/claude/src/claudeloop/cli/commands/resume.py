# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer

from claudeloop import bootstrap
from claudeloop.application.usecases.resume_session import (
    resolve_most_recent,
    resume_explicit,
)
from claudeloop.cli.asyncio import async_command
from claudeloop.cli.render import render_session_warning
from claudeloop.cli.time_parse import parse_wind_down_at
from claudeloop.domain.errors import InvalidSessionSelectorError
from claudeloop.infrastructure.config import load_config
from claudeloop.infrastructure.logging import configure_logging
from claudeloop.infrastructure.stream_ui import BufferingStreamUi, run_textual_app


def resume(
    session_id: str | None = typer.Option(
        None, "--session-id", help="Resume this specific session id"
    ),
    cwd_dir: Path | None = typer.Option(
        None,
        "--cwd",
        exists=True,
        file_okay=False,
        help="Effective working directory for bootstrap (default: current directory)",
    ),
    max_turns: int | None = typer.Option(None, "--max-turns"),
    max_dollars: float | None = typer.Option(None, "--max-dollars"),
    max_wait_seconds: float | None = typer.Option(None, "--max-wait"),
    model: str | None = typer.Option(
        None, "--model", help="Alias (low|medium|high) or raw Anthropic model id"
    ),
    effort: str | None = typer.Option(None, "--effort", help="Effort: low|medium|high|xhigh|max"),
    preset: str | None = typer.Option(None, "--preset", help="Preset low|medium|high"),
    continue_prompt: str | None = typer.Option(None, "--continue-prompt"),
    done_marker: str | None = typer.Option(None, "--done-marker"),
    log_level: str = typer.Option("INFO", "--log-level"),
    log_file: Path | None = typer.Option(None, "--log-file"),
    log_chatter: str | None = typer.Option(None, "--log-chatter"),
    auto_model: bool = typer.Option(True, "--auto-model/--no-auto-model"),
    stream_ui: bool = typer.Option(False, "--stream-ui"),
    wind_down_at_spec: str | None = typer.Option(
        None,
        "--wind-down-at",
        help="Wind down at this deadline (ISO8601 timestamp or +duration like +2h, +90m)",
    ),
) -> None:
    """Resume a Claude Code session and run it autonomously to completion.
    With --session-id, resumes that specific session. Without it, auto-selects
    the most recently modified session for the current directory and prints a
    warning banner naming exactly which one before doing anything."""
    _resume(
        session_id=session_id,
        cwd_dir=cwd_dir,
        max_turns=max_turns,
        max_dollars=max_dollars,
        max_wait_seconds=max_wait_seconds,
        model=model,
        effort=effort,
        preset=preset,
        continue_prompt=continue_prompt,
        done_marker=done_marker,
        log_level=log_level,
        log_file=log_file,
        log_chatter=log_chatter,
        auto_model=auto_model,
        stream_ui=stream_ui,
        wind_down_at_spec=wind_down_at_spec,
    )


@async_command
async def _resume(
    *,
    session_id: str | None,
    cwd_dir: Path | None,
    max_turns: int | None,
    max_dollars: float | None,
    max_wait_seconds: float | None,
    model: str | None,
    effort: str | None,
    preset: str | None,
    continue_prompt: str | None,
    done_marker: str | None,
    log_level: str,
    log_file: Path | None,
    log_chatter: str | None,
    auto_model: bool,
    stream_ui: bool,
    wind_down_at_spec: str | None,
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    wind_down_at: datetime | None = None
    if wind_down_at_spec is not None:
        try:
            wind_down_at = parse_wind_down_at(wind_down_at_spec, now=datetime.now(timezone.utc))
        except ValueError as exc:
            typer.echo(f"Invalid --wind-down-at: {exc}", err=True)
            raise typer.Exit(code=2) from exc
    config = load_config(
        cwd=cwd,
        cli_overrides={
            "max_turns": max_turns,
            "max_dollars": max_dollars,
            "max_wait_seconds": max_wait_seconds,
            "model": model,
            "effort": effort,
            "preset": preset,
            "log_level": log_level,
            "log_chatter": log_chatter,
            "done_marker": done_marker,
            "log_file": str(log_file) if log_file else None,
            "auto_model": auto_model,
            "stream_ui": stream_ui,
        },
    )
    structlog_path = log_file or (Path(config.log_file) if config.log_file else None)
    configure_logging(
        log_file=structlog_path,
        level=config.log_level or log_level,
        human_console=not stream_ui,
    )

    resolved_id = session_id
    if resolved_id is None:
        catalog = bootstrap.build_session_catalog()
        try:
            ref = resolve_most_recent(catalog, str(cwd))
        except InvalidSessionSelectorError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        typer.echo(render_session_warning(ref, str(cwd)), err=True)
        resolved_id = ref.session_id

    live_ui = BufferingStreamUi() if stream_ui else None
    context = bootstrap.build_runner(
        cwd=cwd,
        config=config,
        session_id=resolved_id,
        resume=resolved_id,
        log_file=structlog_path,
        stream_ui=live_ui,
        wind_down_at=wind_down_at,
    )
    typer.echo(f"Run id: {context.run_id}", err=True)
    typer.echo(f"Trace id: {context.trace_id}", err=True)

    if stream_ui:
        import asyncio
        import threading

        def _ui() -> None:
            try:
                run_textual_app(
                    events_path=context.run_dir.events_path,
                    follow=True,
                    live_source=live_ui,
                    initial=live_ui.state if live_ui else None,
                )
            except RuntimeError as exc:
                typer.echo(str(exc), err=True)

        threading.Thread(target=_ui, daemon=True).start()
        await asyncio.sleep(0)

    result = await resume_explicit(
        context.runner,
        continue_prompt=continue_prompt or "Continue exactly where you left off.",
    )

    if not result.success:
        typer.echo(f"Run failed: {result.reason}", err=True)
        if "stopped" in result.reason:
            raise typer.Exit(code=130)
        raise typer.Exit(code=1)
    typer.echo(f"Done: {result.reason}")

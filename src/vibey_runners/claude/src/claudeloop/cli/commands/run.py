# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer

from claudeloop import bootstrap
from claudeloop.application.usecases.run_plan import parse_plan_file, run_from_plan_file
from claudeloop.cli.asyncio import async_command
from claudeloop.cli.time_parse import parse_wind_down_at
from claudeloop.domain.errors import InvalidPlanError
from claudeloop.domain.handoff_marker import (
    EXIT_WIND_DOWN,
    HANDOFF_MARKER_FILENAME,
)
from claudeloop.infrastructure.config import load_config
from claudeloop.infrastructure.logging import configure_logging
from claudeloop.infrastructure.stream_ui import BufferingStreamUi, run_textual_app


def _parse_connector(spec: str) -> tuple[str, Any]:
    if "=" not in spec:
        raise ValueError(f"connector must be NAME=JSON or NAME=url, got {spec!r}")
    name, _, value = spec.partition("=")
    name = name.strip()
    value = value.strip()
    if not name:
        raise ValueError(f"connector name must not be blank in {spec!r}")
    if value.startswith("{"):
        return name, json.loads(value)
    return name, {"url": value}


def run(
    plan_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="Markdown plan file to seed a fresh session with"
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Name this run instead of generating an id (lets a supervisor attach while it runs)",
    ),
    cwd_dir: Path | None = typer.Option(
        None,
        "--cwd",
        exists=True,
        file_okay=False,
        help="Effective working directory for bootstrap (default: current directory)",
    ),
    attach: list[Path] = typer.Option(
        None, "--attach", help="Attach file or directory (repeatable)"
    ),
    add_folder: list[Path] = typer.Option(
        None, "--add-folder", help="Extra workspace folder (repeatable)"
    ),
    from_github: str | None = typer.Option(
        None, "--from-github", help="GitHub repo OWNER/REPO[@REF]"
    ),
    skill: list[str] = typer.Option(None, "--skill", help="Skill name (repeatable)"),
    plugin: list[str] = typer.Option(None, "--plugin", help="Plugin name (repeatable)"),
    connector: list[str] = typer.Option(
        None, "--connector", help="Connector NAME=JSON or NAME=url (repeatable)"
    ),
    append_system_prompt: list[str] = typer.Option(
        None, "--append-system-prompt", help="Append text to the system prompt (repeatable)"
    ),
    import_issue: str | None = typer.Option(
        None, "--import-issue", help="GitHub issue OWNER/REPO#N"
    ),
    web_search: bool = typer.Option(False, "--web-search", help="Enable web search tools"),
    deep_research: bool = typer.Option(False, "--deep-research", help="Enable deep research mode"),
    permission_mode: str = typer.Option(
        "bypass", "--permission-mode", help="Permission mode for the agent SDK"
    ),
    slash: str | None = typer.Option(
        None, "--slash", help="Initial slash command (must start with /)"
    ),
    max_turns: int | None = typer.Option(None, "--max-turns"),
    max_dollars: float | None = typer.Option(None, "--max-dollars"),
    max_wait_seconds: float | None = typer.Option(None, "--max-wait"),
    model: str | None = typer.Option(
        None, "--model", help="Alias (low|medium|high) or raw Anthropic model id"
    ),
    effort: str | None = typer.Option(
        None, "--effort", help="Effort: low|medium|high|xhigh|max (default medium)"
    ),
    preset: str | None = typer.Option(
        None, "--preset", help="Preset low|medium|high (sets model+effort; flags override)"
    ),
    continue_prompt: str | None = typer.Option(
        None,
        "--continue-prompt",
        help="Prompt used on subsequent turns (default: continue where you left off)",
    ),
    done_marker: str | None = typer.Option(
        None, "--done-marker", help="Fallback completion marker substring"
    ),
    log_level: str = typer.Option("INFO", "--log-level"),
    log_file: Path | None = typer.Option(
        None,
        "--log-file",
        help="structlog JSON file (separate from per-run audit/events under .claudeloop/runs/)",
    ),
    log_chatter: str | None = typer.Option(
        None, "--log-chatter", help="Chatter verbosity: full|summary|off"
    ),
    auto_model: bool = typer.Option(
        True,
        "--auto-model/--no-auto-model",
        help="Automatic model/effort escalate and cost-aware downgrade (default on)",
    ),
    stream_ui: bool = typer.Option(
        False,
        "--stream-ui",
        help="Full-screen Textual multi-pane token stream UI (requires a TTY)",
    ),
    max_buffer_size: int | None = typer.Option(
        None,
        "--max-buffer-size",
        help=(
            "Claude Agent SDK JSON message buffer in bytes (default 50MiB). "
            "Raise if you see 'JSON message exceeded maximum buffer size of 1048576'."
        ),
    ),
    wind_down_at_spec: str | None = typer.Option(
        None,
        "--wind-down-at",
        help="Wind down at this deadline (ISO8601 timestamp or +duration like +2h, +90m)",
    ),
) -> None:
    """Seed a brand-new Claude Code session from PLAN_FILE and run it
    autonomously to completion — across turns, across rate-limit windows,
    across a credits top-up — never blocking on a human. See
    docs/guides/autonomous-runs.md."""
    _run(
        plan_file=plan_file,
        run_id=run_id,
        cwd_dir=cwd_dir,
        attach=attach,
        add_folder=add_folder,
        from_github=from_github,
        skills=skill,
        plugins=plugin,
        connectors=connector,
        append_system_prompts=append_system_prompt,
        import_issue=import_issue,
        web_search=web_search,
        deep_research=deep_research,
        permission_mode=permission_mode,
        slash=slash,
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
        max_buffer_size=max_buffer_size,
        wind_down_at_spec=wind_down_at_spec,
    )


@async_command
async def _run(
    *,
    plan_file: Path,
    run_id: str | None,
    cwd_dir: Path | None,
    attach: list[Path] | None,
    add_folder: list[Path] | None,
    from_github: str | None,
    skills: list[str] | None,
    plugins: list[str] | None,
    connectors: list[str] | None,
    append_system_prompts: list[str] | None,
    import_issue: str | None,
    web_search: bool,
    deep_research: bool,
    permission_mode: str,
    slash: str | None,
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
    max_buffer_size: int | None,
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
    connector_map: dict[str, Any] = {}
    if connectors:
        for spec in connectors:
            try:
                name, cfg = _parse_connector(spec)
            except (ValueError, json.JSONDecodeError) as exc:
                typer.echo(f"Invalid --connector: {exc}", err=True)
                raise typer.Exit(code=2) from exc
            connector_map[name] = cfg
    if slash is not None and not slash.startswith("/"):
        typer.echo("--slash must start with '/'", err=True)
        raise typer.Exit(code=2)
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
            "max_buffer_size": max_buffer_size,
            "auto_model": auto_model,
            "stream_ui": stream_ui,
            "permission_mode": permission_mode,
            "web_search": web_search,
            "deep_research": deep_research,
        },
    )
    structlog_path = log_file or (Path(config.log_file) if config.log_file else None)
    configure_logging(
        log_file=structlog_path,
        level=config.log_level or log_level,
        human_console=not stream_ui,
    )

    try:
        plan = parse_plan_file(plan_file)
    except InvalidPlanError as exc:
        typer.echo(f"Invalid plan file: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    # Combine multiple --append-system-prompt values with blank lines
    combined_append = "\n\n".join(append_system_prompts) if append_system_prompts else None

    live_ui = BufferingStreamUi() if stream_ui else None
    try:
        context = bootstrap.build_runner(
            cwd=cwd,
            config=config,
            log_file=structlog_path,
            plan=plan,
            plan_path=plan_file,
            stream_ui=live_ui,
            attach=attach,
            add_folders=add_folder,
            skills=skills,
            plugins=plugins,
            connectors=connector_map or None,
            from_github=from_github,
            import_issue=import_issue,
            slash=slash,
            run_id=run_id,
            append_system_prompt=combined_append,
            wind_down_at=wind_down_at,
        )
    except ValueError as exc:
        typer.echo(f"{exc}", err=True)
        raise typer.Exit(code=2) from exc
    except FileExistsError as exc:
        typer.echo(
            f"Run id {run_id!r} already exists; pick another or use `claudeloop resume`.",
            err=True,
        )
        raise typer.Exit(code=2) from exc
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

        thread = threading.Thread(target=_ui, daemon=True)
        thread.start()
        await asyncio.sleep(0)

    try:
        result = await run_from_plan_file(
            context.runner,
            plan_file,
            continue_prompt=continue_prompt or "Continue exactly where you left off.",
            done_marker=config.done_marker,
        )
    except InvalidPlanError as exc:
        typer.echo(f"Invalid plan file: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not result.success:
        if result.reason.startswith("wind-down:"):
            # Not a failure: the run handed its work over on purpose. A distinct
            # exit code is how a supervisor tells "resume me elsewhere" from
            # "this failed" without parsing the reason string.
            typer.echo(f"Wound down: {result.reason}", err=True)
            marker = context.run_dir.root / HANDOFF_MARKER_FILENAME
            if marker.is_file():
                typer.echo(f"Handoff: {marker}", err=True)
            raise typer.Exit(code=EXIT_WIND_DOWN)
        typer.echo(f"Run failed: {result.reason}", err=True)
        if "stopped" in result.reason:
            summary = context.run_dir.stop_summary_path
            if summary.is_file():
                typer.echo(f"Stop summary: {summary}", err=True)
            raise typer.Exit(code=130)
        raise typer.Exit(code=1)
    typer.echo(f"Done: {result.reason}")

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap
from agyloop.application.usecases.resume_session import resolve_last_run, resume_explicit
from agyloop.cli.asyncio import async_command
from agyloop.domain.errors import InvalidSessionSelectorError


def resume(
    conversation: Annotated[
        str | None,
        typer.Option(
            "--conversation",
            help="Resume this Antigravity conversation_id from the local .agyloop/ registry.",
        ),
    ] = None,
    last: Annotated[
        bool,
        typer.Option("--last", help="Resume the most recent run in the local .agyloop/ registry."),
    ] = False,
    cwd_dir: Annotated[
        Path | None,
        typer.Option(
            "--cwd",
            exists=True,
            file_okay=False,
            help="Working directory whose .agyloop/runs registry to read.",
        ),
    ] = None,
    model: Annotated[str | None, typer.Option("--model")] = None,
    max_turns: Annotated[int | None, typer.Option("--max-turns")] = None,
    max_wait_seconds: Annotated[float | None, typer.Option("--max-wait")] = None,
    no_probe: Annotated[
        bool,
        typer.Option(
            "--no-probe",
            help="Wait only to computed quota boundaries; issue zero probe requests.",
        ),
    ] = False,
    ramp: Annotated[
        int,
        typer.Option(
            "--ramp",
            min=0,
            help="Pace the first N turns (sleep attempt seconds) against acceleration 429s.",
        ),
    ] = 0,
    gateway: Annotated[
        str,
        typer.Option(
            "--gateway",
            help="Agent transport: sdk (default) or cli (live agy subprocess).",
        ),
    ] = "sdk",
    max_dollars: Annotated[
        float | None,
        typer.Option("--max-dollars", help="Labeled USD estimate cap (ADR 0009)."),
    ] = None,
) -> None:
    """Resume an agyloop-managed conversation. Uses LocalAgentConfig(conversation_id=…).

    If resumption fails, starts a fresh conversation seeded with persisted plan state.
    """
    _resume(
        conversation=conversation,
        last=last,
        cwd_dir=cwd_dir,
        model=model,
        max_turns=max_turns,
        max_wait_seconds=max_wait_seconds,
        no_probe=no_probe,
        ramp=ramp,
        gateway=gateway,
        max_dollars=max_dollars,
    )


@async_command
async def _resume(
    *,
    conversation: str | None,
    last: bool,
    cwd_dir: Path | None,
    model: str | None,
    max_turns: int | None,
    max_wait_seconds: float | None,
    no_probe: bool,
    ramp: int,
    gateway: str,
    max_dollars: float | None,
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        kind = bootstrap.parse_gateway(gateway)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    catalog = bootstrap.build_session_catalog()
    conversation_id = conversation
    if conversation_id is None or last:
        try:
            ref = resolve_last_run(catalog, str(cwd))
        except InvalidSessionSelectorError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        if conversation_id is None:
            conversation_id = ref.session_id
        typer.echo(
            f"Resuming last registry run conversation_id={ref.session_id} cwd={ref.cwd}",
            err=True,
        )

    context = bootstrap.build_runner(
        cwd=cwd,
        conversation_id=conversation_id,
        model=model,
        max_turns=max_turns,
        max_wait_seconds=max_wait_seconds,
        no_probe=no_probe,
        resume=True,
        ramp=ramp,
        gateway=kind,
        max_dollars=max_dollars,
    )
    typer.echo(f"Run id: {context.run_id}", err=True)
    result = await resume_explicit(context.runner)
    if not result.success:
        typer.echo(f"Run failed: {result.reason}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Done: {result.reason}")

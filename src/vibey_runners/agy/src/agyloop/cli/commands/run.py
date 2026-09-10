# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap
from agyloop.application.usecases.run_plan import parse_plan_file, run_from_plan_file
from agyloop.cli.asyncio import async_command
from agyloop.domain.errors import InvalidPlanError, UnsafeSkipPermissionsError


def run(
    plan_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            help="Markdown plan file to seed a fresh Antigravity session.",
        ),
    ],
    run_id: Annotated[
        str | None,
        typer.Option(
            "--run-id",
            help="Name this run instead of generating an id (lets a supervisor attach mid-run).",
        ),
    ] = None,
    cwd_dir: Annotated[
        Path | None,
        typer.Option(
            "--cwd",
            exists=True,
            file_okay=False,
            help="Working directory for the run (default: current directory).",
        ),
    ] = None,
    model: Annotated[str | None, typer.Option("--model", help="Gemini model id or alias.")] = None,
    max_turns: Annotated[int | None, typer.Option("--max-turns")] = None,
    max_wait_seconds: Annotated[float | None, typer.Option("--max-wait")] = None,
    max_tokens: Annotated[int | None, typer.Option("--max-tokens")] = None,
    no_probe: Annotated[
        bool,
        typer.Option(
            "--no-probe",
            help="Wait only to computed quota boundaries; issue zero probe requests.",
        ),
    ] = False,
    strict_autonomy: Annotated[bool, typer.Option("--strict-autonomy")] = False,
    safe: Annotated[bool, typer.Option("--safe", help="Nondestructive tools only.")] = False,
    yolo: Annotated[
        bool, typer.Option("--yolo", help="Drop workspace/destructive scopes.")
    ] = False,
    unsafe_skip_permissions: Annotated[
        bool,
        typer.Option(
            "--unsafe-skip-permissions",
            help=(
                "Refused on --gateway sdk. On --gateway cli, maps to "
                "agy --dangerously-skip-permissions after root/git/sandbox gates. "
                "Never combined with --sandbox (antigravity-cli#36)."
            ),
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
            help="Agent transport: sdk (default, google-antigravity) or cli (live agy subprocess).",
        ),
    ] = "sdk",
    add_dir: Annotated[
        list[Path] | None,
        typer.Option("--add-dir", help="Extra workspace directory (repeatable)."),
    ] = None,
    max_dollars: Annotated[
        float | None,
        typer.Option(
            "--max-dollars",
            help="Stop when labeled USD estimate reaches this cap (ADR 0009).",
        ),
    ] = None,
    preset: Annotated[
        str | None,
        typer.Option("--preset", help="low | medium | high (sets model + effort)."),
    ] = None,
    effort: Annotated[
        str | None, typer.Option("--effort", help="low|medium|high|xhigh|max.")
    ] = None,
    scoped: Annotated[
        bool, typer.Option("--scoped", help="Workspace + destructive denies without allow_all.")
    ] = False,
) -> None:
    """Seed a brand-new Antigravity session from PLAN_FILE and run it unattended."""
    _run(
        plan_file=plan_file,
        run_id=run_id,
        cwd_dir=cwd_dir,
        model=model,
        max_turns=max_turns,
        max_wait_seconds=max_wait_seconds,
        max_tokens=max_tokens,
        no_probe=no_probe,
        strict_autonomy=strict_autonomy,
        safe=safe,
        yolo=yolo,
        unsafe_skip_permissions=unsafe_skip_permissions,
        ramp=ramp,
        gateway=gateway,
        add_dir=add_dir,
        max_dollars=max_dollars,
        preset=preset,
        effort=effort,
        scoped=scoped,
    )


@async_command
async def _run(
    *,
    plan_file: Path,
    run_id: str | None,
    cwd_dir: Path | None,
    model: str | None,
    max_turns: int | None,
    max_wait_seconds: float | None,
    max_tokens: int | None,
    no_probe: bool,
    strict_autonomy: bool,
    safe: bool,
    yolo: bool,
    unsafe_skip_permissions: bool,
    ramp: int,
    gateway: str,
    add_dir: list[Path] | None,
    max_dollars: float | None,
    preset: str | None,
    effort: str | None,
    scoped: bool,
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        kind = bootstrap.parse_gateway(gateway)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if unsafe_skip_permissions:
        try:
            if kind == "sdk":
                bootstrap.refuse_unsafe_skip_on_sdk_path(cwd)
            else:
                bootstrap.validate_unsafe_skip_permissions(cwd)
        except UnsafeSkipPermissionsError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
    try:
        plan = parse_plan_file(plan_file)
    except InvalidPlanError as exc:
        typer.echo(f"Invalid plan file: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    permission_mode = (
        "yolo" if yolo else ("safe" if safe else ("scoped" if scoped else "autonomous"))
    )
    context = bootstrap.build_runner(
        cwd=cwd,
        run_id=run_id,
        plan=plan,
        plan_path=plan_file,
        model=model,
        max_turns=max_turns,
        max_wait_seconds=max_wait_seconds,
        max_tokens=max_tokens,
        no_probe=no_probe,
        strict_autonomy=strict_autonomy,
        permission_mode=permission_mode,
        ramp=ramp,
        gateway=kind,
        unsafe_skip_permissions=unsafe_skip_permissions,
        add_dirs=[str(path) for path in add_dir] if add_dir else None,
        max_dollars=max_dollars,
        preset=preset,
        effort=effort,
    )
    typer.echo(f"Run id: {context.run_id}", err=True)
    result = await run_from_plan_file(context.runner, plan_file)
    if not result.success:
        typer.echo(f"Run failed: {result.reason}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Done: {result.reason}")

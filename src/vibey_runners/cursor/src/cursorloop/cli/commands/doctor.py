# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from cursorloop.application.usecases.doctor import explain_error_payload
from cursorloop.infrastructure.config import load_config
from cursorloop.infrastructure.doctor_env import findings_as_json, run_doctor


def doctor(
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
    as_json: bool = typer.Option(False, "--json", help="Emit findings as JSON"),
    explain_error: Path | None = typer.Option(
        None,
        "--explain-error",
        exists=True,
        readable=True,
        help="Classify a captured error payload offline",
    ),
    model: str | None = typer.Option(None, "--model", help="Model profile or id to validate"),
    cloud: bool = typer.Option(False, "--cloud", help="Also check cloud-hooks dirty state"),
    offline: bool = typer.Option(
        False, "--offline", help="Skip live Cursor.me / models.list checks"
    ),
) -> None:
    """Fail-fast preflight checks before a multi-hour unattended run."""
    if explain_error is not None:
        try:
            name = explain_error_payload(explain_error)
        except (OSError, ValueError, TypeError) as exc:
            typer.echo(f"Could not classify payload: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        typer.echo(name)
        raise typer.Exit(code=0)

    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    config = load_config()
    findings = run_doctor(
        workspace=cwd,
        api_key=config.api_key,
        model=model or config.model,
        cloud=cloud,
        live=not offline,
    )
    if as_json:
        typer.echo(findings_as_json(findings), nl=False)
    else:
        for finding in findings:
            typer.echo(f"[{finding.level}] {finding.name}: {finding.detail}")
            if finding.remedy:
                typer.echo(f"  remedy: {finding.remedy}")
    if any(f.level == "fail" for f in findings):
        raise typer.Exit(code=1)

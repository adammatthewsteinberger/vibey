# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop doctor`` — pre-flight environment checks."""

from __future__ import annotations

from pathlib import Path

import typer

from codexloop.bootstrap import run_doctor_checks


def doctor(
    cwd: Path | None = typer.Option(None, "--cwd", help="Working directory to check."),
) -> None:
    """Report auth mode, probe strategies, and other pre-flight gates."""
    report = run_doctor_checks(cwd=cwd)
    typer.echo(f"auth_mode: {report.auth_mode}")
    strategies = ", ".join(
        f"{name}={'live' if live else 'unavailable'}"
        for name, live in report.probe_strategies.items()
    )
    typer.echo(f"probe_strategies: {strategies}")
    for check in report.checks:
        mark = "ok" if check.passed else "FAIL"
        typer.echo(f"[{mark}] {check.name}: {check.detail}")
    if not report.all_passed:
        raise typer.Exit(1)

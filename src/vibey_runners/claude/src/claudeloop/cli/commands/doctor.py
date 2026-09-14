# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap
from claudeloop.application.usecases.doctor import all_passed, run_doctor
from claudeloop.cli.render import render_doctor_checks

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def doctor(ctx: typer.Context) -> None:
    """Pre-flight checks before starting a long unattended run: Claude Code
    installed and authenticated, configured MCP servers, working-directory
    safety. Run this BEFORE `run`/`resume`, not instead of them."""
    if ctx.invoked_subcommand is not None:
        return
    env = bootstrap.build_doctor_environment()
    checks = run_doctor(env, cwd=Path.cwd())
    typer.echo(render_doctor_checks(checks))
    if not all_passed(checks):
        raise typer.Exit(code=1)

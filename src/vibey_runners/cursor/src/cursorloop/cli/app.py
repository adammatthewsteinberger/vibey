# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Typer root app and console-script entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from cursorloop import __version__, bootstrap
from cursorloop.cli.commands.agents import agents, hooks, models, usage, whoami
from cursorloop.cli.commands.cloud import cloud_app
from cursorloop.cli.commands.control_cmds import (
    logs,
    prompt,
    reset,
    runs,
    savepoints,
    snapshot,
    status,
    stop,
    unwind,
    watch,
    wind_down,
)
from cursorloop.cli.commands.doctor import doctor
from cursorloop.cli.commands.resume import resume
from cursorloop.cli.commands.run import run
from cursorloop.cli.man_page import render_man_page
from cursorloop.domain.verbosity import resolve_log_plan

app = typer.Typer(
    name="cursorloop",
    help=(
        "Onion-architected, autonomous Cursor Agent session runner — never "
        "blocks on a human, distinguishes rate-limit windows from exhausted "
        "credits, and resumes safely across usage windows."
    ),
    add_completion=False,
    no_args_is_help=True,
)

app.command(name="run")(run)
app.command(name="resume")(resume)
app.command(name="stop")(stop)
app.command(name="wind-down")(wind_down)
app.command(name="prompt")(prompt)
app.command(name="status")(status)
app.command(name="logs")(logs)
app.command(name="watch")(watch)
app.command(name="runs")(runs)
app.command(name="savepoints")(savepoints)
app.command(name="unwind")(unwind)
app.command(name="snapshot")(snapshot)
app.command(name="reset")(reset)
app.command(name="agents")(agents)
app.command(name="models")(models)
app.command(name="usage")(usage)
app.command(name="whoami")(whoami)
app.command(name="hooks")(hooks)
app.command(name="doctor")(doctor)
app.add_typer(cloud_app, name="cloud")


def main() -> int:
    try:
        app(prog_name="cursorloop")
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1
    return 0


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"cursorloop {__version__}")
        raise typer.Exit(code=0)


def _man_callback(value: bool) -> None:
    if value:
        typer.echo(render_man_page())
        raise typer.Exit(code=0)


@app.callback()
def _root(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    man: bool = typer.Option(
        False,
        "--man",
        callback=_man_callback,
        is_eager=True,
        help="Show the man-page style reference and exit",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="More detail: -v debug, -vv also third-party libraries, -vvv full payloads.",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Warnings and errors only."),
    log_level: str | None = typer.Option(
        None, "--log-level", help="DEBUG, INFO, WARNING, ERROR or CRITICAL. Overrides -v."
    ),
    log_file: Path | None = typer.Option(
        None, "--log-file", help="Also write redacted JSON lines to this file."
    ),
) -> None:
    del version, man
    try:
        plan = resolve_log_plan(verbose=verbose, quiet=quiet, log_level=log_level)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    bootstrap.configure_cli_logging(plan=plan, log_file=log_file)

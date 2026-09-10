# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Typer root app and console-script entry point.

Registered in pyproject.toml as:
    [project.scripts]
    codexloop = "codexloop.cli.app:main"
"""

from __future__ import annotations

from pathlib import Path

import typer

from codexloop import __version__, bootstrap
from codexloop.bootstrap import build_api_typer_app
from codexloop.cli.commands.approval_cmd import approval_cmd
from codexloop.cli.commands.capacity import capacity
from codexloop.cli.commands.cwd_cmd import cwd_cmd
from codexloop.cli.commands.doctor import doctor
from codexloop.cli.commands.effort_cmd import effort_cmd
from codexloop.cli.commands.logs import logs
from codexloop.cli.commands.model_cmd import model_cmd
from codexloop.cli.commands.prompt import prompt
from codexloop.cli.commands.reset import reset
from codexloop.cli.commands.resume import resume
from codexloop.cli.commands.run import run
from codexloop.cli.commands.runs import runs
from codexloop.cli.commands.sandbox_cmd import sandbox_cmd
from codexloop.cli.commands.savepoints import savepoints
from codexloop.cli.commands.snapshot import snapshot
from codexloop.cli.commands.status import status
from codexloop.cli.commands.stop import stop
from codexloop.cli.commands.threads import threads
from codexloop.cli.commands.unwind import unwind
from codexloop.cli.commands.watch import watch
from codexloop.cli.commands.wind_down_cmd import wind_down
from codexloop.domain.verbosity import resolve_log_plan

app = typer.Typer(
    name="codexloop",
    help=(
        "Onion-architected, autonomous OpenAI Codex session runner — never "
        "blocks on a human, distinguishes rate limits from exhausted credits, "
        "and resumes safely across usage windows."
    ),
    add_completion=False,
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"codexloop {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the installed codexloop version and exit.",
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
    del version
    try:
        plan = resolve_log_plan(verbose=verbose, quiet=quiet, log_level=log_level)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    bootstrap.configure_cli_logging(plan=plan, log_file=log_file)


app.command()(run)
app.command()(resume)
app.command()(threads)
app.command()(status)
app.command()(logs)
app.command()(runs)
app.command()(prompt)
app.command()(stop)
app.command(name="wind-down")(wind_down)
app.command()(capacity)
app.command()(doctor)
app.command()(watch)
app.command()(savepoints)
app.command()(unwind)
app.command()(reset)
app.command()(snapshot)
app.command("model")(model_cmd)
app.command("effort")(effort_cmd)
app.command("approval")(approval_cmd)
app.command("sandbox")(sandbox_cmd)
app.command("cwd")(cwd_cmd)
app.add_typer(build_api_typer_app(), name="api")


def main() -> None:  # pragma: no cover — process entrypoint
    app()


if __name__ == "__main__":  # pragma: no cover
    main()

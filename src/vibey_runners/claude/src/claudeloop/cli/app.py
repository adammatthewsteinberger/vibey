# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The Typer root app and console-script entry point.

Registered in pyproject.toml as:
    [project.scripts]
    claudeloop = "claudeloop.cli.app:main"
"""

from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import __version__, bootstrap
from claudeloop.bootstrap import build_api_click_group
from claudeloop.cli.commands.artifact_cmd import app as artifact_app
from claudeloop.cli.commands.attach_cmd import attach, unattach
from claudeloop.cli.commands.chat_cmd import app as chat_app
from claudeloop.cli.commands.connector_cmd import app as connector_app
from claudeloop.cli.commands.cwd_cmd import cwd_cmd
from claudeloop.cli.commands.doctor import app as doctor_app
from claudeloop.cli.commands.effort_cmd import effort_cmd
from claudeloop.cli.commands.folder_cmd import app as folder_app
from claudeloop.cli.commands.github_cmd import app as github_app
from claudeloop.cli.commands.logs import logs
from claudeloop.cli.commands.memory_cmd import app as memory_app
from claudeloop.cli.commands.model_cmd import model_cmd
from claudeloop.cli.commands.permission_mode import permission_mode
from claudeloop.cli.commands.plugin_cmd import app as plugin_app
from claudeloop.cli.commands.preset_cmd import preset_cmd
from claudeloop.cli.commands.prompt import prompt
from claudeloop.cli.commands.research_cmd import app as research_app
from claudeloop.cli.commands.reset import reset
from claudeloop.cli.commands.response_cmd import app as response_app
from claudeloop.cli.commands.resume import resume
from claudeloop.cli.commands.run import run
from claudeloop.cli.commands.runs import app as runs_app
from claudeloop.cli.commands.savepoints import app as savepoints_app
from claudeloop.cli.commands.sessions import app as sessions_app
from claudeloop.cli.commands.skill_cmd import app as skill_app
from claudeloop.cli.commands.slash_cmd import slash_cmd
from claudeloop.cli.commands.snapshot_cmd import snapshot
from claudeloop.cli.commands.status import status
from claudeloop.cli.commands.stop import stop
from claudeloop.cli.commands.tool_cmd import app as tool_app
from claudeloop.cli.commands.unwind import unwind
from claudeloop.cli.commands.voice_cmd import app as voice_app
from claudeloop.cli.commands.voice_cmd import speak
from claudeloop.cli.commands.watch import watch
from claudeloop.cli.commands.web_search_cmd import web_search_cmd
from claudeloop.cli.commands.wind_down_cmd import wind_down
from claudeloop.cli.man_page import write_man_page
from claudeloop.domain.verbosity import resolve_log_plan


def _root_wants_man_help(argv: list[str]) -> bool:
    """True for ``claudeloop --help`` / ``-h`` / ``--man`` with no subcommand."""
    return len(argv) == 2 and argv[1] in ("--help", "-h", "--man")


app = typer.Typer(
    name="claudeloop",
    help=(
        "Onion-architected, autonomous Claude Code session runner — never "
        "blocks on a human, distinguishes rate limits from exhausted credits, "
        "and resumes safely across usage windows."
    ),
    add_completion=False,
    no_args_is_help=True,
)

app.command(name="run")(run)
app.command(name="resume")(resume)
app.command(name="stop")(stop)
app.command(name="wind-down")(wind_down)
app.command(name="prompt")(prompt)
app.command(name="model")(model_cmd)
app.command(name="effort")(effort_cmd)
app.command(name="preset")(preset_cmd)
app.command(name="permission-mode")(permission_mode)
app.command(name="cwd")(cwd_cmd)
app.command(name="slash")(slash_cmd)
app.add_typer(tool_app, name="tool")
app.command(name="attach")(attach)
app.command(name="unattach")(unattach)
app.add_typer(folder_app, name="folder")
app.add_typer(skill_app, name="skill")
app.add_typer(plugin_app, name="plugin")
app.add_typer(connector_app, name="connector")
app.add_typer(github_app, name="github")
app.add_typer(research_app, name="research")
app.command(name="web-search")(web_search_cmd)
app.add_typer(memory_app, name="memory")
app.add_typer(artifact_app, name="artifact")
app.add_typer(chat_app, name="chat")
app.add_typer(response_app, name="response")
app.add_typer(voice_app, name="voice")
app.command(name="speak")(speak)
app.command(name="logs")(logs)
app.command(name="status")(status)
app.command(name="snapshot")(snapshot)
app.command(name="unwind")(unwind)
app.command(name="reset")(reset)
app.command(name="watch")(watch)
app.add_typer(runs_app, name="runs")
app.add_typer(savepoints_app, name="savepoints")
app.add_typer(sessions_app, name="sessions")
app.add_typer(doctor_app, name="doctor")


@app.command(
    "api",
    help="Generated 1:1 Anthropic SDK REST surface — run `claudeloop api <resource> ...`.",
    add_help_option=False,
)
def api_stub() -> None:
    """Show the generated API command tree."""
    build_api_click_group()(["--help"])


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"claudeloop {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the installed claudeloop version and exit.",
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
    del version  # handled entirely by the eager callback above
    try:
        plan = resolve_log_plan(verbose=verbose, quiet=quiet, log_level=log_level)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    bootstrap.configure_cli_logging(plan=plan, log_file=log_file)


def main() -> int:
    import sys

    import click

    if _root_wants_man_help(sys.argv):
        write_man_page()
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "api":
        group = build_api_click_group()
        try:
            group.main(args=sys.argv[2:], prog_name="claudeloop api", standalone_mode=True)
        except click.exceptions.Exit as exc:
            code = 0 if exc.exit_code is None else exc.exit_code
            raise SystemExit(code) from exc
        return 0
    app(prog_name="claudeloop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

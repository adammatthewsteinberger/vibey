# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap
from agyloop.application.usecases.list_sessions import list_sessions
from agyloop.cli.render import render_session_list

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def sessions(
    ctx: typer.Context,
    cwd: Annotated[
        str | None,
        typer.Option("--cwd", help="Directory whose .agyloop/runs registry to list."),
    ] = None,
) -> None:
    """List agyloop's local run registry under .agyloop/runs/.

    This cannot enumerate vendor conversations. Only runs this tool created
    are shown — there is no API to list Antigravity IDE or other conversations.
    """
    if ctx.invoked_subcommand is not None:
        return
    catalog = bootstrap.build_session_catalog()
    resolved = cwd if cwd is not None else str(Path.cwd())
    refs = list_sessions(catalog, resolved)
    typer.echo(render_session_list(refs))

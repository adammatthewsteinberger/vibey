# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap

app = typer.Typer(help="List agyloop run directories under .agyloop/runs/")


@app.callback(invoke_without_command=True)
def runs(
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    rows = bootstrap.list_runs(cwd)
    if not rows:
        typer.echo("No runs found.")
        return
    for row in rows:
        typer.echo(
            f"{row['run_id']}  {row['status']:<10}  phase={row['phase']}  "
            f"attempt={row['attempt']}  pid={row['pid']}"
        )

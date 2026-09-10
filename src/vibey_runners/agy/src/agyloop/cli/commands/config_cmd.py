# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def config_cmd(
    cwd_dir: Annotated[Path | None, typer.Option("--cwd", exists=True, file_okay=False)] = None,
) -> None:
    """Print the effective runner config (file + AGYLOOP_* + defaults)."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    cfg = bootstrap.effective_config(cwd)
    for key, value in cfg.items():
        typer.echo(f"{key}: {value}")

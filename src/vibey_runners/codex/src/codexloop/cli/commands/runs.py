# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop runs``."""

from __future__ import annotations

import typer

from codexloop.bootstrap import list_run_records
from codexloop.cli.render import render_runs


def runs() -> None:
    """List run directories under .codexloop/runs/."""
    typer.echo(render_runs(list_run_records()))

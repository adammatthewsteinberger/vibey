# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop threads`` — this product's run registry, not vendor sessions."""

from __future__ import annotations

import typer

from codexloop.application.usecases.list_threads import list_threads
from codexloop.bootstrap import build_runner
from codexloop.cli.render import render_threads


def threads() -> None:
    """List this product's run registry (not vendor Codex sessions)."""
    ctx = build_runner(ensure_run=False)
    typer.echo(render_threads(list_threads(ctx)))

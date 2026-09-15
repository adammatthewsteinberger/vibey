# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Partial Cloud Agents CLI — loudly incomplete pending a stable OpenAPI pin."""

from __future__ import annotations

import typer

from cursorloop.infrastructure.api.binder import bind_partial_commands
from cursorloop.infrastructure.api.registry import DEFERRED_REASON

cloud_app = typer.Typer(
    name="cloud",
    help=(
        "Cloud Agents REST commands (PARTIAL — ADR-0006). Not a complete API "
        "surface; full generation awaits a digest-stable published OpenAPI doc."
    ),
    no_args_is_help=True,
)


@cloud_app.callback()
def _cloud_root() -> None:
    """Announce deferral once when the cloud group is invoked."""
    return None


@cloud_app.command("status")
def status() -> None:
    """Explain the M4 deferral / partial surface."""
    typer.echo(DEFERRED_REASON)


bind_partial_commands(cloud_app)

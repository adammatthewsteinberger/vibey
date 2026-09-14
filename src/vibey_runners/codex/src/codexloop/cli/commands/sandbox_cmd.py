# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop sandbox`` — enqueue SetSandbox."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.approval import SandboxMode
from codexloop.domain.control import SetSandbox
from codexloop.domain.errors import ConfigurationError


def sandbox_cmd(
    sandbox: str = typer.Argument(..., help="Sandbox mode."),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """Queue a sandbox-mode change for the next control boundary."""
    try:
        value = SandboxMode(sandbox)
        path = enqueue_run_control(SetSandbox(sandbox=value), run_id=run_id)
    except (ConfigurationError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued → {path}")

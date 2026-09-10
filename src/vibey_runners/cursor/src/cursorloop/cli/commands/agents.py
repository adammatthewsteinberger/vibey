# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure.agent.hooks import ManagedHooks


def agents(
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    """List local agents for a workspace (requires a live Cursor client)."""
    del cwd_dir
    typer.echo("Use a live Cursor client; listing is available once the SDK bridge is connected.")


def models() -> None:
    """List shipped model profile aliases."""
    for name, profile in SHIPPED_PRESETS.items():
        typer.echo(f"{name}\t{profile.model_id}")


def usage() -> None:
    """Show usage for the active agent (requires a live client)."""
    typer.echo("Usage requires a live Cursor client session.")


def whoami() -> None:
    """Show the authenticated Cursor account (requires a live client)."""
    typer.echo("whoami requires a live Cursor client session.")


def hooks(
    action: str = typer.Argument("status", help="status | install | restore | diff"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    """Inspect or manage the autonomy hooks fragment."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    manager = ManagedHooks(workspace=cwd, state_dir=cwd / ".cursorloop")
    if action == "status":
        typer.echo("installed" if manager.is_installed() else "not-installed")
    elif action == "install":
        manager.install()
        typer.echo("hooks installed")
    elif action == "restore":
        ok = manager.restore()
        typer.echo("restored" if ok else "not-restored")
    elif action == "diff":
        typer.echo(manager.diff() or "(no diff)")
    else:
        typer.echo(f"unknown action: {action}", err=True)
        raise typer.Exit(code=2)

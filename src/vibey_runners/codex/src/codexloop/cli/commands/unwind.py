# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop unwind`` — reset the worktree to a save point."""

from __future__ import annotations

import typer

from codexloop.bootstrap import unwind_savepoint
from codexloop.domain.errors import ConfigurationError


def unwind(
    to: str = typer.Argument(..., help="Save point number, sha prefix, or label."),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Keep a backup ref."),
) -> None:
    """Hard-reset to a save point. Refuses while a run is live."""
    try:
        result = unwind_savepoint(to, run_id=run_id, backup=backup)
    except (ConfigurationError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"restored {result.restored_sha} (savepoint {result.to.n})")
    if result.backup_ref:
        typer.echo(f"backup {result.backup_ref}")

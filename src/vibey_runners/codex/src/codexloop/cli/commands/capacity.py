# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop capacity`` — print plan windows or say they are unavailable."""

from __future__ import annotations

import typer

from codexloop.bootstrap import read_capacity_windows


def capacity() -> None:
    """Show ChatGPT plan windows when known; say so honestly when not."""
    windows = read_capacity_windows()
    if windows is None:
        typer.echo("plan windows unavailable")
        return
    typer.echo(f"plan_type: {windows.plan_type or 'unknown'}")
    typer.echo(f"limit_reached: {windows.limit_reached or 'none'}")
    if windows.primary is None:
        typer.echo("primary: unavailable")
    else:
        p = windows.primary
        typer.echo(
            f"primary: used={p.used_percent}% window={p.window_minutes}m "
            f"resets_at={p.resets_at.isoformat() if p.resets_at else 'unknown'}"
        )
    if windows.secondary is None:
        typer.echo("secondary: unavailable")
    else:
        s = windows.secondary
        typer.echo(
            f"secondary: used={s.used_percent}% window={s.window_minutes}m "
            f"resets_at={s.resets_at.isoformat() if s.resets_at else 'unknown'}"
        )

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def snapshot(
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id"),
    out: Path | None = typer.Option(None, "--out", help="Copy the snapshot JSON to this path"),
    bundle: bool = typer.Option(
        True,
        "--bundle/--no-bundle",
        help="Also write a portable bundle under snapshots/bundles/",
    ),
) -> None:
    """Write a handoff snapshot for the active (or specified) run.

    Always writes control-plane JSON under ``.claudeloop/runs/<id>/snapshots/``
    and publishes ``snapshot_path`` / ``snapshot_digest`` on the state bus.
    Claude Code transcripts are included best-effort when discoverable.
    """
    cwd = Path.cwd()
    try:
        ref = bootstrap_ops.emit_snapshot(cwd, run_id=run_id, bundle=bundle, out=out)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"snapshot_path: {ref.path}")
    typer.echo(f"snapshot_digest: {ref.digest}")
    if ref.bundle_path:
        typer.echo(f"bundle_path: {ref.bundle_path}")
    if out is not None:
        typer.echo(f"copied_to: {out}")

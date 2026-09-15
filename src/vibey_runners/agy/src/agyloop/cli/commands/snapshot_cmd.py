# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap


def snapshot(
    run_id: Annotated[str | None, typer.Option("--run-id", help="Target run id")] = None,
    out: Annotated[
        Path | None, typer.Option("--out", help="Copy the snapshot JSON to this path")
    ] = None,
    bundle: Annotated[
        bool,
        typer.Option(
            "--bundle/--no-bundle",
            help="Also write a portable bundle under snapshots/bundles/",
        ),
    ] = True,
    cwd_dir: Annotated[
        Path | None,
        typer.Option("--cwd", exists=True, file_okay=False),
    ] = None,
) -> None:
    """Write a handoff snapshot for the active (or specified) run."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        ref = bootstrap.emit_snapshot(cwd, run_id=run_id, bundle=bundle, out=out)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"snapshot_path: {ref.path}")
    typer.echo(f"snapshot_digest: {ref.digest}")
    if ref.bundle_path:
        typer.echo(f"bundle_path: {ref.bundle_path}")
    if out is not None:
        typer.echo(f"copied_to: {out}")

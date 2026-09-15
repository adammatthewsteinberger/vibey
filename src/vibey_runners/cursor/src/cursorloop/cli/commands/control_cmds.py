# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path

import typer

from cursorloop.infrastructure import run_control
from cursorloop.infrastructure.agent.hooks import ManagedHooks
from cursorloop.infrastructure.git_savepoints import GitSavePointStore
from cursorloop.infrastructure.rundir import list_run_directories, resolve_run_directory
from cursorloop.infrastructure.snapshot import FileRunSnapshotSink
from cursorloop.infrastructure.stream_ui import StreamUiApp


def stop(
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    """Request a soft stop of the active (or specified) run."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = run_control.enqueue_stop(cwd, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Stop requested for run {result.run_id}")


def wind_down(
    reason: str = typer.Option("operator wind-down", "--reason"),
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    """Request a wind-down: finish current turn, write handoff marker, exit 75."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        result = run_control.enqueue_wind_down(cwd, reason, run_id)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Wind-down requested for run {result.run_id}")


def prompt(
    text: str = typer.Argument(..., help="Prompt text for the next turn"),
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    result = run_control.enqueue_prompt(cwd, text, run_id)
    typer.echo(f"Prompt queued for run {result.run_id}")


def status(
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    directory = resolve_run_directory(cwd, run_id)
    meta = directory.read_meta()
    typer.echo(json.dumps(meta.to_dict(), indent=2))


def logs(
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    directory = resolve_run_directory(cwd, run_id)
    if directory.audit_path.is_file():
        typer.echo(directory.audit_path.read_text(encoding="utf-8"), nl=False)


def watch(
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
    ui: bool = typer.Option(False, "--ui", help="Launch the Textual stream UI when available"),
) -> None:
    """Tail the run event stream (plain text; optional Textual UI via --ui)."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    directory = resolve_run_directory(cwd, run_id)
    text = ""
    if directory.events_path.is_file():
        text = directory.events_path.read_text(encoding="utf-8")
        typer.echo(text, nl=False)
    if ui:
        app_ui = StreamUiApp()
        for line in text.splitlines():
            app_ui.on_delta(line)
        app_ui.run()


def runs(
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    for directory in list_run_directories(cwd):
        meta = directory.read_meta()
        typer.echo(f"{meta.run_id}\t{meta.status}\t{meta.phase or '-'}")


def savepoints(
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    directory = resolve_run_directory(cwd, run_id)
    store = GitSavePointStore(cwd=cwd, index_path=directory.savepoints_path)
    for point in store.list_points(directory.read_meta().run_id):
        typer.echo(f"{point.n}\t{point.sha[:12]}\t{point.label}")


def unwind(
    to: str = typer.Option(..., "--to", help="Savepoint SHA or ref"),
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    directory = resolve_run_directory(cwd, run_id)
    store = GitSavePointStore(cwd=cwd, index_path=directory.savepoints_path)
    store.unwind(run_id=directory.read_meta().run_id, to=to, backup=True)
    typer.echo(f"Unwound to {to}")


def snapshot(
    reason: str = typer.Option("manual", "--reason"),
    run_id: str | None = typer.Option(None, "--run-id"),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    directory = resolve_run_directory(cwd, run_id)
    ref = FileRunSnapshotSink(directory.snapshots_root, run_id=directory.read_meta().run_id).emit(
        reason
    )
    if ref is not None:
        typer.echo(f"Snapshot {ref.digest} -> {ref.path}")


def reset(
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    """Restore managed hooks after a crashed run."""
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    ok = ManagedHooks(workspace=cwd, state_dir=cwd / ".cursorloop").restore()
    typer.echo("hooks restored" if ok else "nothing to restore")

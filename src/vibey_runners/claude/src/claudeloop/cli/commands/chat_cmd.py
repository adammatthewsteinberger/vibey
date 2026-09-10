# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="Native chat/session metadata under .claudeloop/chats/")


@app.command("list")
def list_cmd() -> None:
    rows = bootstrap_ops.chat_list(Path.cwd())
    if not rows:
        typer.echo("No chats.")
        return
    for row in rows:
        alias = row.get("alias") or row.get("session_id")
        flags = []
        if row.get("pinned"):
            flags.append("pinned")
        if row.get("unread"):
            flags.append("unread")
        suffix = f" ({', '.join(flags)})" if flags else ""
        typer.echo(f"{row.get('session_id')}  {alias}{suffix}")


@app.command("show")
def show(
    session_id: str = typer.Argument(..., help="Session id"),
) -> None:
    meta = bootstrap_ops.chat_show(Path.cwd(), session_id)
    typer.echo(json.dumps(meta, indent=2))


@app.command("rename")
def rename(
    session_id: str = typer.Argument(..., help="Session id"),
    alias: str = typer.Argument(..., help="New alias"),
) -> None:
    meta = bootstrap_ops.chat_rename(Path.cwd(), session_id, alias)
    typer.echo(f"Renamed {session_id} → {meta.get('alias')}")


@app.command("delete")
def delete(
    session_id: str = typer.Argument(..., help="Session id"),
) -> None:
    if bootstrap_ops.chat_delete(Path.cwd(), session_id):
        typer.echo(f"Deleted chat metadata for {session_id}")
    else:
        typer.echo(f"No chat metadata for {session_id}", err=True)
        raise typer.Exit(code=1)


@app.command("pin")
def pin(
    session_id: str = typer.Argument(..., help="Session id"),
) -> None:
    bootstrap_ops.chat_pin(Path.cwd(), session_id)
    typer.echo(f"Pinned {session_id}")


@app.command("unpin")
def unpin(
    session_id: str = typer.Argument(..., help="Session id"),
) -> None:
    bootstrap_ops.chat_unpin(Path.cwd(), session_id)
    typer.echo(f"Unpinned {session_id}")


@app.command("unread")
def unread(
    session_id: str = typer.Argument(..., help="Session id"),
) -> None:
    bootstrap_ops.chat_unread(Path.cwd(), session_id)
    typer.echo(f"Marked {session_id} unread")


@app.command("read")
def read_cmd(
    session_id: str = typer.Argument(..., help="Session id"),
) -> None:
    bootstrap_ops.chat_read(Path.cwd(), session_id)
    typer.echo(f"Marked {session_id} read")


@app.command("share")
def share(
    session_id: str = typer.Argument(..., help="Session id"),
) -> None:
    result = bootstrap_ops.chat_share(Path.cwd(), session_id)
    typer.echo(f"Share token: {result['share_token']}")
    typer.echo(f"Local share bundle: {result['bundle_path']}")
    typer.echo("(Local export only — not a Claude.ai share link. Distribute the bundle yourself.)")


@app.command("project")
def project(
    session_id: str = typer.Argument(..., help="Session id"),
    project_name: str = typer.Argument(..., help="Project label"),
) -> None:
    meta = bootstrap_ops.chat_project(Path.cwd(), session_id, project_name)
    typer.echo(f"Set project for {session_id}: {meta.get('project')}")

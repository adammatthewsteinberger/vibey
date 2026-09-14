# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops

app = typer.Typer(help="GitHub repo and issue resources for the active run")


@app.command("add")
def add(
    repo_ref: str = typer.Argument(..., help="OWNER/REPO or OWNER/REPO@REF"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
            action="add",
            kind="github",
            value=repo_ref,
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued github add for run {result.run_id}: {repo_ref}")


@app.command("import-issue")
def import_issue(
    issue_ref: str = typer.Argument(..., help="OWNER/REPO#N"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    try:
        result = bootstrap_ops.enqueue_resource(
            Path.cwd(),
            action="add",
            kind="issue",
            value=issue_ref,
            run_id=run_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued github import-issue for run {result.run_id}: {issue_ref}")

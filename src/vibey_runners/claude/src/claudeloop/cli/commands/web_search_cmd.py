# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from claudeloop import bootstrap_ops


def web_search_cmd(
    query: str = typer.Argument(..., help="Web search query"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Enable web search and inject the query as an immediate prompt."""
    cwd = Path.cwd()
    try:
        bootstrap_ops.enqueue_resource(
            cwd,
            action="add",
            kind="web-search",
            value=query,
            run_id=run_id,
        )
        result = bootstrap_ops.enqueue_prompt(cwd, query, immediate=True, run_id=run_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Queued web-search + prompt_now for run {result.run_id}")

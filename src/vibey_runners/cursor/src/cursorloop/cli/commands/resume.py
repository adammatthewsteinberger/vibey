# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import typer

from cursorloop import bootstrap
from cursorloop.application.usecases.run_plan import run_from_plan_file
from cursorloop.cli.asyncio import async_command
from cursorloop.cli.render import exit_code_for
from cursorloop.domain.autonomy import autonomy_preamble
from cursorloop.infrastructure.config import load_config


def resume(
    agent_id: str = typer.Option(..., "--agent-id", help="Existing Cursor agent id"),
    plan: Path | None = typer.Option(None, "--plan", exists=True, readable=True),
    cwd_dir: Path | None = typer.Option(None, "--cwd", exists=True, file_okay=False),
) -> None:
    """Resume an existing agent and continue the autonomous loop."""
    _resume(agent_id=agent_id, plan=plan, cwd_dir=cwd_dir)


@async_command
async def _resume(
    *,
    agent_id: str,
    plan: Path | None,
    cwd_dir: Path | None,
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    config = load_config()
    built = bootstrap.build_runner(cwd=cwd, config=config, plan_path=plan, resume_agent_id=agent_id)
    try:
        if plan is not None:
            result = await run_from_plan_file(built.runner, plan)
        else:
            result = await built.runner.run(autonomy_preamble() + "Continue the unfinished work.")
    finally:
        built.close()
    if not result.success:
        typer.echo(f"Run failed: {result.reason}", err=True)
        raise typer.Exit(code=exit_code_for(result))
    typer.echo(f"Done: {result.reason}")

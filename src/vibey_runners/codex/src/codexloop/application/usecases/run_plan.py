# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: drive a new run from a markdown work plan."""

from __future__ import annotations

from codexloop.application.dto import RunResult
from codexloop.application.runner import AutonomousRunner, RunnerContext
from codexloop.domain.session import SessionSelector


async def run_plan(ctx: RunnerContext, selector: SessionSelector, plan: str) -> RunResult:
    return await AutonomousRunner(ctx).run(selector, plan)

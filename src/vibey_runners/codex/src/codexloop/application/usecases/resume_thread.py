# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: resume an existing thread by explicit id."""

from __future__ import annotations

from codexloop.application.dto import RunResult
from codexloop.application.runner import AutonomousRunner, RunnerContext
from codexloop.domain.session import Explicit


async def resume_thread(ctx: RunnerContext, thread_id: str, plan: str = "") -> RunResult:
    return await AutonomousRunner(ctx).run(Explicit(thread_id), plan)

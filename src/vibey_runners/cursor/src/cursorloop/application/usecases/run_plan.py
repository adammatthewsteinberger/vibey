# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: seed a fresh run from a plan file and drive it to completion."""

from __future__ import annotations

from pathlib import Path

from cursorloop.application.dto import RunResult
from cursorloop.application.runner import AutonomousRunner
from cursorloop.domain.autonomy import autonomy_preamble
from cursorloop.domain.plan import WorkPlan


def parse_plan_file(plan_path: Path) -> WorkPlan:
    return WorkPlan.parse(plan_path.read_text(encoding="utf-8"))


async def run_from_plan_file(runner: AutonomousRunner, plan_path: Path) -> RunResult:
    plan = parse_plan_file(plan_path)
    runner.attach_plan(plan)
    return await runner.run(autonomy_preamble() + plan.raw_text)

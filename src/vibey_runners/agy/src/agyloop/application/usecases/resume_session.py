# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use cases: resume a conversation from the local .agyloop/ run registry."""

from __future__ import annotations

from agyloop.application.dto import RunResult
from agyloop.application.ports import SessionCatalog
from agyloop.application.runner import AutonomousRunner
from agyloop.application.usecases.run_plan import with_done_marker_instruction
from agyloop.domain.errors import InvalidSessionSelectorError
from agyloop.domain.session import SessionRef


async def resume_explicit(
    runner: AutonomousRunner,
    *,
    continue_prompt: str = "Continue exactly where you left off.",
) -> RunResult:
    prompt = with_done_marker_instruction(continue_prompt)
    return await runner.run(initial_prompt=prompt, continue_prompt=prompt)


def resolve_last_run(catalog: SessionCatalog, cwd: str) -> SessionRef:
    ref = catalog.most_recent(cwd)
    if ref is None:
        raise InvalidSessionSelectorError(
            f"No prior agyloop runs found under .agyloop/runs/ for this directory ({cwd}). "
            "Pass a plan file to `agyloop run`, or --conversation to target a specific id. "
            "Vendor conversations cannot be enumerated."
        )
    return ref

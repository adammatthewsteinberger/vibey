# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use cases: resume a specific session, or auto-select the most recently
modified one for a working directory."""

from __future__ import annotations

from claudeloop.application.dto import RunResult
from claudeloop.application.ports import SessionCatalog
from claudeloop.application.runner import AutonomousRunner
from claudeloop.application.usecases.run_plan import with_done_marker_instruction
from claudeloop.domain.errors import InvalidSessionSelectorError
from claudeloop.domain.session import SessionRef


async def resume_explicit(
    runner: AutonomousRunner,
    *,
    continue_prompt: str = "Continue exactly where you left off.",
) -> RunResult:
    """Resume via a session_id the AgentGateway was already constructed with
    (see infrastructure/agent/gateway.py — resume/continuation is an option
    passed at ClaudeAgentOptions construction time, not per-call)."""
    prompt = with_done_marker_instruction(continue_prompt)
    return await runner.run(initial_prompt=prompt, continue_prompt=prompt)


def resolve_most_recent(catalog: SessionCatalog, cwd: str) -> SessionRef:
    ref = catalog.most_recent(cwd)
    if ref is None:
        raise InvalidSessionSelectorError(
            f"No prior Claude Code sessions found for this directory ({cwd}). "
            "Pass a plan file to start fresh, or --session-id to target a specific "
            "session."
        )
    return ref

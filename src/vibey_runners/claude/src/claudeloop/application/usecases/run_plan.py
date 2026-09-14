# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: seed a fresh session from a plan file and run it to completion."""

from __future__ import annotations

from pathlib import Path

from claudeloop.application.dto import RunResult
from claudeloop.application.runner import AutonomousRunner
from claudeloop.domain.completion import DEFAULT_DONE_MARKER
from claudeloop.domain.plan import WorkPlan

_DONE_INSTRUCTION_TEMPLATE = (
    "{prompt}\n\n"
    "---\n"
    "Process note (from the automation running you, not the user): this session "
    "may be resumed automatically across multiple turns if you get cut off. "
    "If, and only if, the ENTIRE task above is now fully complete with nothing "
    "left to do, end your final message with this exact line on its own: "
    "{marker}\n"
    "If any work remains -- including work you were mid-way through -- do NOT "
    "include that line, so the automation knows to resume you."
)


def with_done_marker_instruction(prompt_text: str, done_marker: str = DEFAULT_DONE_MARKER) -> str:
    """Ported from legacy/claude_autoresume.py's with_done_marker_instruction()
    (lines 232-248) as the fallback path for models without structured output."""
    return _DONE_INSTRUCTION_TEMPLATE.format(prompt=prompt_text, marker=done_marker)


async def run_from_plan_file(
    runner: AutonomousRunner,
    plan_path: Path,
    *,
    continue_prompt: str = "Continue exactly where you left off.",
    done_marker: str | None = None,
) -> RunResult:
    raw_text = plan_path.read_text(encoding="utf-8")
    plan = WorkPlan.parse(raw_text)
    marker = done_marker or DEFAULT_DONE_MARKER
    initial_prompt = with_done_marker_instruction(plan.raw_text, done_marker=marker)
    continue_with_marker = with_done_marker_instruction(continue_prompt, done_marker=marker)
    return await runner.run(initial_prompt=initial_prompt, continue_prompt=continue_with_marker)


def parse_plan_file(plan_path: Path) -> WorkPlan:
    return WorkPlan.parse(plan_path.read_text(encoding="utf-8"))

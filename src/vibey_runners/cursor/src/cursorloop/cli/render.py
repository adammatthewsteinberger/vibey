# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Map RunResult reasons to stable process exit codes."""

from __future__ import annotations

from cursorloop.application.dto import RunResult
from cursorloop.domain.handoff_marker import EXIT_WIND_DOWN

# 0 complete; 1 failed; 2 usage (Typer); 3 auth; 4 max wait; 75 wind-down; 130 interrupted


def exit_code_for(result: RunResult) -> int:
    if result.success:
        return 0
    reason = result.reason.lower()
    if "wind-down" in reason:
        return EXIT_WIND_DOWN
    if "authentication failed" in reason:
        return 3
    if "max wait exceeded" in reason:
        return 4
    if "stopped" in reason:
        return 130
    return 1

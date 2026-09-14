# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Turn-level signals consumed by capacity classification."""

from __future__ import annotations

from dataclasses import dataclass

from codexloop.domain.capacity import PlanWindows


@dataclass(frozen=True, slots=True)
class TurnSignals:
    """Bundle of independent turn signals assembled at the infrastructure edge."""

    error_code: str | None = None
    error_type: str | None = None
    http_status: int | None = None
    retry_after_s: float | None = None
    plan_windows: PlanWindows | None = None
    completed: bool = False
    failed: bool = False
    final_message: str | None = None
    structured_output: object | None = None
    usage: object | None = None
    exit_code: int | None = None
    stderr_tail: str | None = None

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Application DTOs. ``TurnSignals`` lives in domain and is re-exported here."""

from __future__ import annotations

from dataclasses import dataclass

from codexloop.domain.capacity import CapacityState, PlanWindows
from codexloop.domain.signals import TurnSignals

__all__ = ["ProbeResult", "RunResult", "TokenUsage", "TurnOutcome", "TurnSignals"]


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    signals: TurnSignals | None = None
    usage: TokenUsage | None = None
    exit_code: int | None = None
    thread_id: str | None = None
    cost_dollars: float = 0.0


@dataclass(frozen=True, slots=True)
class ProbeResult:
    outcome: CapacityState
    snapshot: PlanWindows | None = None


@dataclass(frozen=True, slots=True)
class RunResult:
    success: bool
    reason: str
    turns: int
    thread_id: str | None

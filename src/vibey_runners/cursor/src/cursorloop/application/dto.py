# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Data transfer objects passed between application/ and adapters.

Not domain value objects — these carry the raw shape of one agent turn
before domain.classify.classify() and domain.completion.evaluate() reduce
them to CapacityState / CompletionVerdict. ``cost_usd is None`` means
UNKNOWN, never zero; ``cost_pending`` is propagated from the usage reader.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from cursorloop.domain.classify import TurnSignals
from cursorloop.domain.completion import StructuredVerdict


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    """What one real or probe turn produced, translated from raw agent events."""

    signals: TurnSignals
    verdict: StructuredVerdict | None
    output_text: str
    agent_id: str | None = None
    run_id: str | None = None
    tokens: int = 0
    cost_usd: float | None = None
    cost_pending: bool = True
    raw_events: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class ProbeResult:
    signals: TurnSignals
    at: datetime


@dataclass(frozen=True, slots=True)
class RunResult:
    success: bool
    reason: str
    agent_id: str | None
    turns_spent: int
    tokens_spent: int
    dollars_spent: float
    cost_pending: bool

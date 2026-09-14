# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Data transfer objects passed between application/ and infrastructure/ adapters.
Not domain value objects — these carry the raw shape of one SDK interaction
before domain.classify.classify() and domain.completion.evaluate() reduce them
to CapacityState / CompletionVerdict."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.completion import StructuredVerdict


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    """What one real or probe turn produced, translated from raw SDK messages
    by infrastructure/agent/translate.py."""

    signals: TurnSignals
    verdict: StructuredVerdict | None
    output_text: str
    session_id: str | None
    cost_usd: float = 0.0
    raw_events: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class ProbeResult:
    signals: TurnSignals
    at: datetime


@dataclass(frozen=True, slots=True)
class RunResult:
    success: bool
    reason: str
    session_id: str | None
    turns_spent: int
    dollars_spent: float

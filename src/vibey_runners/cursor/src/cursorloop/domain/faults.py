# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Gateway-local faults that are deliberately not capacity states.

These values must never reach the capacity wait policy. They are handled in the
runner before the state machine sees a ``CapacityState``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TransientFault:
    kind: str
    attempt_hint: int


@dataclass(frozen=True, slots=True)
class Busy:
    agent_id: str
    active_run_id: str | None


@dataclass(frozen=True, slots=True)
class ConfigFault:
    detail: str
    help_url: str | None = None


Fault = TransientFault | Busy | ConfigFault

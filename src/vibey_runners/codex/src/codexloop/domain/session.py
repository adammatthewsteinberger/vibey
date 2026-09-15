# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Thread identity and how a run selects a session."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ThreadRef:
    thread_id: str
    cwd: str
    started_at: datetime
    model: str


@dataclass(frozen=True, slots=True)
class PlanFile:
    path: str


@dataclass(frozen=True, slots=True)
class MostRecent:
    pass


@dataclass(frozen=True, slots=True)
class Explicit:
    thread_id: str


SessionSelector = PlanFile | MostRecent | Explicit

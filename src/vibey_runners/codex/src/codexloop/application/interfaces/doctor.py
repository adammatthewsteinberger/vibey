# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""What `doctor` needs from the outside world, and the vocabulary it answers in.

The result types live here alongside the Protocol: they are part of the seam's
vocabulary, not of the use case that consumes it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class DoctorReport:
    checks: tuple[DoctorCheck, ...]
    auth_mode: str
    probe_strategies: Mapping[str, bool] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        return all(check.passed for check in self.checks)


@runtime_checkable
class DoctorEnvironment(Protocol):
    def diagnose(self, *, cwd: Path) -> DoctorReport: ...

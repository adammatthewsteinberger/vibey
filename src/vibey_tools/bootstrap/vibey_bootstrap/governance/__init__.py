"""Governance — budget guards and usage tracking."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from vibey_bootstrap.counters import bump_counter


@dataclass
class BudgetCheck:
    allowed: bool
    remaining_usd: float
    period: str


@dataclass
class _BudgetState:
    budget_usd: float
    spent_usd: float = 0.0
    reserved_usd: float = 0.0


class BudgetGuard:
    """Per-project/period spend cap (Denial-of-Wallet defense)."""

    def __init__(self) -> None:
        self._budgets: dict[tuple[str, str], _BudgetState] = {}
        self._lock = threading.Lock()

    def set_budget(self, project: str, period: str, budget_usd: float) -> None:
        with self._lock:
            self._budgets[(project, period)] = _BudgetState(budget_usd=budget_usd)

    def check(self, project: str, period: str, estimated_usd: float) -> BudgetCheck:
        with self._lock:
            state = self._budgets.get((project, period), _BudgetState(budget_usd=float("inf")))
            remaining = state.budget_usd - state.spent_usd - state.reserved_usd
            allowed = estimated_usd <= remaining
        if not allowed:
            bump_counter("governance.budget.denied")
        return BudgetCheck(allowed=allowed, remaining_usd=max(0.0, remaining), period=period)

    def commit(self, project: str, period: str, actual_usd: float) -> None:
        with self._lock:
            key = (project, period)
            if key not in self._budgets:
                self._budgets[key] = _BudgetState(budget_usd=float("inf"))
            self._budgets[key].spent_usd += actual_usd
            self._budgets[key].reserved_usd = max(0.0, self._budgets[key].reserved_usd - actual_usd)
        bump_counter("governance.budget.committed", int(actual_usd * 1000))


_default_guard = BudgetGuard()


def budget_guard(
    project: str,
    period: str,
    estimated_usd: float,
    *,
    guard: BudgetGuard | None = None,
) -> BudgetCheck:
    return (guard or _default_guard).check(project, period, estimated_usd)


@dataclass
class UsageRecord:
    service: str
    units: float
    unit_type: str
    timestamp: float = field(default_factory=time.time)


class UsageTracker:
    """Generalized multi-service usage meter."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []
        self._lock = threading.Lock()

    def track(self, service: str, units: float, unit_type: str) -> None:
        with self._lock:
            self._records.append(UsageRecord(service=service, units=units, unit_type=unit_type))
        bump_counter(f"governance.usage.{service}.{unit_type}", int(units))

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "service": r.service,
                    "units": r.units,
                    "unit_type": r.unit_type,
                    "timestamp": r.timestamp,
                }
                for r in self._records
            ]


_default_tracker = UsageTracker()


def track_usage(
    service: str, units: float, unit_type: str, *, tracker: UsageTracker | None = None
) -> None:
    (tracker or _default_tracker).track(service, units, unit_type)


__all__ = ["BudgetCheck", "BudgetGuard", "UsageTracker", "budget_guard", "track_usage"]

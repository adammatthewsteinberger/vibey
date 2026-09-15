"""Governance module tests."""

from __future__ import annotations

from vibey_bootstrap.governance import BudgetGuard, UsageTracker, track_usage


def test_budget_guard_denies_over_budget() -> None:
    guard = BudgetGuard()
    guard.set_budget("proj", "2026-06", 10.0)
    guard.commit("proj", "2026-06", 9.0)
    check = guard.check("proj", "2026-06", 2.0)
    assert check.allowed is False


def test_track_usage_records() -> None:
    tracker = UsageTracker()
    track_usage("openai", 100, "tokens", tracker=tracker)
    snap = tracker.snapshot()
    assert snap[0]["service"] == "openai"

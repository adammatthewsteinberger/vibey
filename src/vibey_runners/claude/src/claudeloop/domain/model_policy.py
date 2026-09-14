# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Automatic model/effort escalate and cost-aware downgrade — pure decisions."""

from __future__ import annotations

from dataclasses import dataclass

from claudeloop.domain.model_profile import (
    ModelAliases,
    ModelEffortProfile,
    downgrade_profile,
    escalate_profile,
    profile_for_preset,
)


@dataclass(frozen=True, slots=True)
class AutoModelDecision:
    profile: ModelEffortProfile | None
    reason: str | None = None


def decide_auto_model(
    current: ModelEffortProfile,
    *,
    consecutive_no_progress: int,
    consecutive_progress: int,
    blocked: bool,
    dollars_spent: float,
    max_dollars: float | None,
    budget_downgrade_done: bool,
    operator_locked: bool,
    auto_enabled: bool,
    aliases: ModelAliases | None = None,
) -> AutoModelDecision:
    """Return a new profile when auto policy fires; None when no change.

    Escalate outranks downgrade in the same decision (hysteresis). Budget
    force-to-low is checked first among downgrades but still loses to escalate.
    """
    if not auto_enabled or operator_locked:
        return AutoModelDecision(profile=None)

    table = aliases or ModelAliases()

    escalate = blocked or consecutive_no_progress >= 2
    if escalate:
        nxt = escalate_profile(current, table)
        if nxt != current:
            reason = "escalate_blocked" if blocked else "escalate_stuck"
            return AutoModelDecision(profile=nxt, reason=reason)
        return AutoModelDecision(profile=None)

    if (
        max_dollars is not None
        and max_dollars > 0
        and not budget_downgrade_done
        and dollars_spent >= 0.8 * max_dollars
    ):
        low = profile_for_preset("low", table)
        if low != current:
            return AutoModelDecision(profile=low, reason="downgrade_budget")
        return AutoModelDecision(profile=None)

    if consecutive_progress >= 2:
        nxt = downgrade_profile(current, table)
        if nxt != current:
            return AutoModelDecision(profile=nxt, reason="downgrade_progress")

    return AutoModelDecision(profile=None)

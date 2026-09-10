# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Automatic model escalate and cost-aware downgrade — pure decisions.

Escalation always emits a matching ``restore`` profile because Cursor per-run
model overrides are sticky: a one-off escalation that is not followed by an
explicit de-escalation bills every later turn at the higher rate. Downgrades
are lasting cost-control changes and do not restore.
"""

from __future__ import annotations

from dataclasses import dataclass

from cursorloop.domain.model_profile import (
    ModelProfile,
    downgrade_profile,
    escalate_profile,
    floor_profile,
)


@dataclass(frozen=True, slots=True)
class AutoModelDecision:
    profile: ModelProfile | None
    reason: str | None = None
    restore: ModelProfile | None = None


def _is_at_or_below_floor(current: ModelProfile, floor: ModelProfile) -> bool:
    if current == floor:
        return True
    stepped = escalate_profile(current)
    # Below the floor: one escalate lands on the floor (composer-fast → composer).
    return stepped == floor and current != floor


def decide_auto_model(
    current: ModelProfile,
    *,
    consecutive_no_progress: int,
    consecutive_progress: int,
    blocked: bool,
    dollars_spent: float,
    max_dollars: float | None,
    budget_downgrade_done: bool,
    operator_locked: bool,
    auto_enabled: bool,
) -> AutoModelDecision:
    """Return a new profile when auto policy fires; None when no change.

    Escalate outranks downgrade in the same decision (hysteresis). Budget
    force-to-low is checked first among downgrades but still loses to escalate.
    """
    if not auto_enabled or operator_locked:
        return AutoModelDecision(profile=None)

    escalate = blocked or consecutive_no_progress >= 2
    if escalate:
        nxt = escalate_profile(current)
        if nxt != current:
            reason = "escalate_blocked" if blocked else "escalate_stuck"
            return AutoModelDecision(profile=nxt, reason=reason, restore=current)
        return AutoModelDecision(profile=None)

    if (
        max_dollars is not None
        and max_dollars > 0
        and not budget_downgrade_done
        and dollars_spent >= 0.8 * max_dollars
    ):
        low = floor_profile(current)
        if not _is_at_or_below_floor(current, low):
            return AutoModelDecision(profile=low, reason="downgrade_budget")
        return AutoModelDecision(profile=None)

    if consecutive_progress >= 2:
        nxt = downgrade_profile(current)
        if nxt != current:
            return AutoModelDecision(profile=nxt, reason="downgrade_progress")

    return AutoModelDecision(profile=None)

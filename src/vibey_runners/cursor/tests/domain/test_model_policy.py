# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from cursorloop.domain.model_policy import AutoModelDecision, decide_auto_model
from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile


def _decide(
    current: ModelProfile,
    *,
    consecutive_no_progress: int = 0,
    consecutive_progress: int = 0,
    blocked: bool = False,
    dollars_spent: float = 0.0,
    max_dollars: float | None = None,
    budget_downgrade_done: bool = False,
    operator_locked: bool = False,
    auto_enabled: bool = True,
) -> AutoModelDecision:
    return decide_auto_model(
        current,
        consecutive_no_progress=consecutive_no_progress,
        consecutive_progress=consecutive_progress,
        blocked=blocked,
        dollars_spent=dollars_spent,
        max_dollars=max_dollars,
        budget_downgrade_done=budget_downgrade_done,
        operator_locked=operator_locked,
        auto_enabled=auto_enabled,
    )


def test_escalation_emits_a_matching_de_escalation() -> None:
    """Per-run model overrides are sticky. A one-off escalation that does not
    emit a matching restore would bill every later turn at the higher rate."""
    current = SHIPPED_PRESETS["composer"]
    decision = _decide(current, consecutive_no_progress=2)
    assert decision.profile is not None
    assert decision.profile != current
    assert decision.restore == current
    assert decision.reason == "escalate_stuck"


def test_blocked_escalation_also_emits_a_matching_restore() -> None:
    current = SHIPPED_PRESETS["composer"]
    decision = _decide(current, blocked=True)
    assert decision.reason == "escalate_blocked"
    assert decision.profile == SHIPPED_PRESETS["grok-4.5"]
    assert decision.restore == current


def test_operator_lock_and_disabled_auto_are_noops() -> None:
    current = SHIPPED_PRESETS["composer"]
    locked = _decide(current, consecutive_no_progress=2, operator_locked=True)
    assert locked.profile is None
    disabled = _decide(current, consecutive_no_progress=5, blocked=True, auto_enabled=False)
    assert disabled.profile is None


def test_escalate_outranks_downgrade() -> None:
    current = SHIPPED_PRESETS["grok"]
    decision = _decide(
        current,
        consecutive_no_progress=2,
        consecutive_progress=2,
        dollars_spent=9.0,
        max_dollars=10.0,
    )
    assert decision.reason == "escalate_stuck"
    assert decision.restore == current


def test_budget_downgrade_forces_the_floor_and_does_not_restore() -> None:
    """A budget downgrade is a lasting cost-control change, not a one-off
    override, so it must not emit a restore to the expensive profile."""
    high = SHIPPED_PRESETS["grok-xhigh"]
    decision = _decide(high, dollars_spent=8.0, max_dollars=10.0)
    assert decision.reason == "downgrade_budget"
    assert decision.profile == SHIPPED_PRESETS["composer"]
    assert decision.restore is None


def test_progress_downgrade_steps_one_rung() -> None:
    high = SHIPPED_PRESETS["grok"]
    decision = _decide(high, consecutive_progress=2, budget_downgrade_done=True)
    assert decision.reason == "downgrade_progress"
    assert decision.profile == SHIPPED_PRESETS["grok-4.5"]
    assert decision.restore is None


def test_budget_already_at_floor_is_noop() -> None:
    low = SHIPPED_PRESETS["composer"]
    decision = _decide(low, dollars_spent=9.0, max_dollars=10.0)
    assert decision.profile is None
    cheaper = _decide(SHIPPED_PRESETS["composer-fast"], dollars_spent=9.0, max_dollars=10.0)
    assert cheaper.profile is None


def test_blocked_at_ceiling_is_noop() -> None:
    at_max = SHIPPED_PRESETS["grok-xhigh"]
    decision = _decide(at_max, blocked=True)
    assert decision.profile is None


def test_progress_already_at_floor_is_noop() -> None:
    low = SHIPPED_PRESETS["composer-fast"]
    decision = _decide(low, consecutive_progress=2)
    assert decision.profile is None


def test_router_budget_downgrade_uses_router_floor() -> None:
    intel = SHIPPED_PRESETS["router-intelligence"]
    decision = _decide(intel, dollars_spent=8.0, max_dollars=10.0)
    assert decision.reason == "downgrade_budget"
    assert decision.profile == SHIPPED_PRESETS["router-cost"]
    assert decision.restore is None


def test_one_stuck_turn_does_not_escalate() -> None:
    decision = _decide(SHIPPED_PRESETS["composer"], consecutive_no_progress=1)
    assert decision.profile is None


def test_budget_path_skipped_when_already_done_or_cap_unset() -> None:
    high = SHIPPED_PRESETS["grok-xhigh"]
    already = _decide(high, dollars_spent=9.0, max_dollars=10.0, budget_downgrade_done=True)
    assert already.profile is None
    unset = _decide(high, dollars_spent=9.0, max_dollars=None)
    assert unset.profile is None

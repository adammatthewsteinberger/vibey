# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for model profile resolution and auto policy."""

from __future__ import annotations

import pytest

from claudeloop.domain.chatter import chatter_event_payload, truncate_chatter
from claudeloop.domain.model_policy import decide_auto_model
from claudeloop.domain.model_profile import (
    DEFAULT_MODEL_HIGH,
    DEFAULT_MODEL_LOW,
    ModelAliases,
    ModelEffortProfile,
    downgrade_profile,
    escalate_profile,
    profile_for_preset,
    resolve_profile,
)


def test_defaults_resolve_to_low_medium() -> None:
    profile = resolve_profile()
    assert profile.model == DEFAULT_MODEL_LOW
    assert profile.effort == "medium"
    assert profile.preset == "low"


def test_preset_high_uses_fable() -> None:
    profile = resolve_profile(preset="high")
    assert profile.model == DEFAULT_MODEL_HIGH
    assert profile.model == "claude-fable-5"
    assert profile.effort == "max"
    assert profile.preset == "high"


def test_model_alias_and_effort_override_preset() -> None:
    profile = resolve_profile(preset="medium", model="high", effort="xhigh")
    assert profile.model == DEFAULT_MODEL_HIGH
    assert profile.effort == "xhigh"
    assert profile.preset == "high"


def test_raw_model_id() -> None:
    profile = resolve_profile(model="claude-haiku-4-5", effort="low")
    assert profile.model == "claude-haiku-4-5"
    assert profile.effort == "low"
    assert profile.preset is None


def test_alias_overrides() -> None:
    aliases = ModelAliases(low="custom-low", medium="custom-med", high="custom-high")
    assert resolve_profile(preset="low", aliases=aliases).model == "custom-low"
    assert resolve_profile(model="medium", aliases=aliases).model == "custom-med"


def test_escalate_and_downgrade_steps() -> None:
    aliases = ModelAliases()
    low = profile_for_preset("low", aliases)
    med = escalate_profile(low, aliases)
    assert med == profile_for_preset("medium", aliases)
    high = escalate_profile(med, aliases)
    assert high.model == DEFAULT_MODEL_HIGH
    bumped = escalate_profile(high, aliases)
    assert bumped.effort == "max" or bumped.effort != high.effort or bumped == high
    # at max effort, escalate is no-op
    at_max = ModelEffortProfile(model=DEFAULT_MODEL_HIGH, effort="max", preset="high")
    assert escalate_profile(at_max, aliases) == at_max
    assert downgrade_profile(high, aliases) == profile_for_preset("medium", aliases)


def test_auto_escalate_stuck_and_operator_lock() -> None:
    current = profile_for_preset("low", ModelAliases())
    decision = decide_auto_model(
        current,
        consecutive_no_progress=2,
        consecutive_progress=0,
        blocked=False,
        dollars_spent=0.0,
        max_dollars=None,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
    )
    assert decision.profile is not None
    assert decision.reason == "escalate_stuck"
    assert decision.profile.preset == "medium"

    locked = decide_auto_model(
        current,
        consecutive_no_progress=2,
        consecutive_progress=0,
        blocked=False,
        dollars_spent=0.0,
        max_dollars=None,
        budget_downgrade_done=False,
        operator_locked=True,
        auto_enabled=True,
    )
    assert locked.profile is None


def test_auto_downgrade_budget_and_progress() -> None:
    high = profile_for_preset("high", ModelAliases())
    budget = decide_auto_model(
        high,
        consecutive_no_progress=0,
        consecutive_progress=0,
        blocked=False,
        dollars_spent=8.0,
        max_dollars=10.0,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
    )
    assert budget.reason == "downgrade_budget"
    assert budget.profile is not None
    assert budget.profile.preset == "low"

    progress = decide_auto_model(
        high,
        consecutive_no_progress=0,
        consecutive_progress=2,
        blocked=False,
        dollars_spent=1.0,
        max_dollars=10.0,
        budget_downgrade_done=True,
        operator_locked=False,
        auto_enabled=True,
    )
    assert progress.reason == "downgrade_progress"
    assert progress.profile == profile_for_preset("medium", ModelAliases())


def test_no_action_when_nothing_warrants_a_change() -> None:
    """No escalate condition, no budget threshold, and fewer than two
    consecutive good turns -- the steady state where auto-model does
    nothing, which no other test reaches (they all hit an earlier branch)."""
    medium = profile_for_preset("medium", ModelAliases())
    decision = decide_auto_model(
        medium,
        consecutive_no_progress=0,
        consecutive_progress=1,
        blocked=False,
        dollars_spent=1.0,
        max_dollars=10.0,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
    )
    assert decision.profile is None
    assert decision.reason is None


def test_progress_downgrade_is_a_no_op_already_at_the_floor() -> None:
    """At the low preset with no further step down, downgrade_profile returns
    the same profile -- decide_auto_model must not report a downgrade that
    doesn't actually change anything."""
    low = profile_for_preset("low", ModelAliases())
    decision = decide_auto_model(
        low,
        consecutive_no_progress=0,
        consecutive_progress=2,
        blocked=False,
        dollars_spent=1.0,
        max_dollars=10.0,
        budget_downgrade_done=True,
        operator_locked=False,
        auto_enabled=True,
    )
    assert decision.profile is None
    assert decision.reason is None


def test_escalate_outranks_downgrade() -> None:
    high = profile_for_preset("medium", ModelAliases())
    decision = decide_auto_model(
        high,
        consecutive_no_progress=2,
        consecutive_progress=2,
        blocked=False,
        dollars_spent=9.0,
        max_dollars=10.0,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
    )
    assert decision.reason == "escalate_stuck"


def test_truncate_chatter() -> None:
    small = truncate_chatter("hi")
    assert small.truncated is False
    big = truncate_chatter("x" * 300_000, cap_bytes=100)
    assert big.truncated is True
    assert len(big.text.encode("utf-8")) <= 100
    # Cap mid multi-byte sequence so the UTF-8 boundary rewind loop runs.
    mid = truncate_chatter("€", cap_bytes=2)  # euro is e2 82 ac
    assert mid.truncated is True
    mid.text.encode("utf-8")


def test_chatter_event_payload_summary_keeps_full_text() -> None:
    assert chatter_event_payload("x", mode="off") is None
    long = "prompt " * 200
    payload = chatter_event_payload(long, mode="summary")
    assert payload is not None
    assert payload["text"] == long
    assert payload["preview_truncated"] is True
    assert len(payload["preview"]) < len(long)
    full = chatter_event_payload("hi", mode="full")
    assert full is not None
    assert full["text"] == "hi"
    assert "preview" not in full
    with_extra = chatter_event_payload("hi", mode="full", extra={"name": "Bash"})
    assert with_extra is not None
    assert with_extra["name"] == "Bash"
    assert with_extra["text"] == "hi"


def test_invalid_effort() -> None:
    with pytest.raises(ValueError):
        resolve_profile(effort="nope")


def test_invalid_preset() -> None:
    with pytest.raises(ValueError):
        resolve_profile(preset="ultra")


def test_blank_model_falls_back_to_low() -> None:
    profile = resolve_profile(model="   ")
    assert profile.model == DEFAULT_MODEL_LOW


def test_downgrade_effort_within_low() -> None:
    aliases = ModelAliases()
    high_effort_low = ModelEffortProfile(model=aliases.low, effort="high", preset="low")
    down = downgrade_profile(high_effort_low, aliases)
    assert down.preset == "low"
    assert down.effort == "medium"


def test_escalate_effort_at_high() -> None:
    aliases = ModelAliases()
    base = ModelEffortProfile(model=aliases.high, effort="high", preset="high")
    up = escalate_profile(base, aliases)
    assert up.effort == "xhigh"
    up2 = escalate_profile(up, aliases)
    assert up2.effort == "max"


def test_auto_disabled() -> None:
    decision = decide_auto_model(
        profile_for_preset("low", ModelAliases()),
        consecutive_no_progress=5,
        consecutive_progress=0,
        blocked=True,
        dollars_spent=99.0,
        max_dollars=10.0,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=False,
    )
    assert decision.profile is None


def test_budget_already_at_low_is_noop() -> None:
    low = profile_for_preset("low", ModelAliases())
    decision = decide_auto_model(
        low,
        consecutive_no_progress=0,
        consecutive_progress=0,
        blocked=False,
        dollars_spent=9.0,
        max_dollars=10.0,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
    )
    assert decision.profile is None


def test_downgrade_from_medium() -> None:
    aliases = ModelAliases()
    assert downgrade_profile(profile_for_preset("medium", aliases), aliases) == profile_for_preset(
        "low", aliases
    )


def test_resolve_model_ref_none() -> None:
    from claudeloop.domain.model_profile import resolve_model_ref

    assert resolve_model_ref(None, ModelAliases()) == DEFAULT_MODEL_LOW


def test_downgrade_custom_model_effort() -> None:
    aliases = ModelAliases()
    custom = ModelEffortProfile(model="claude-haiku-4-5", effort="high", preset=None)
    down = downgrade_profile(custom, aliases)
    assert down.model == "claude-haiku-4-5"
    assert down.effort == "medium"


def test_blocked_at_max_is_noop() -> None:
    at_max = ModelEffortProfile(model=DEFAULT_MODEL_HIGH, effort="max", preset="high")
    decision = decide_auto_model(
        at_max,
        consecutive_no_progress=0,
        consecutive_progress=0,
        blocked=True,
        dollars_spent=0.0,
        max_dollars=None,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
    )
    assert decision.profile is None


def test_progress_already_at_floor_is_noop() -> None:
    low = profile_for_preset("low", ModelAliases())
    decision = decide_auto_model(
        low,
        consecutive_no_progress=0,
        consecutive_progress=2,
        blocked=False,
        dollars_spent=0.0,
        max_dollars=None,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
    )
    assert decision.profile is None


def test_downgrade_custom_at_effort_floor() -> None:
    aliases = ModelAliases()
    custom = ModelEffortProfile(model="claude-haiku-4-5", effort="medium", preset=None)
    down = downgrade_profile(custom, aliases)
    assert down == profile_for_preset("low", aliases)

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for model profile resolution, auto policy, and chatter helpers."""

from __future__ import annotations

import pytest

from agyloop.domain.chatter import chatter_event_payload, truncate_chatter
from agyloop.domain.model_policy import decide_auto_model
from agyloop.domain.model_profile import (
    DEFAULT_MODEL_HIGH,
    DEFAULT_MODEL_LOW,
    ModelAliases,
    ModelEffortProfile,
    downgrade_profile,
    escalate_profile,
    profile_for_preset,
    resolve_model_ref,
    resolve_profile,
)


def test_defaults_resolve_to_low_medium() -> None:
    profile = resolve_profile()
    assert profile.model == DEFAULT_MODEL_LOW
    assert profile.effort == "medium"
    assert profile.preset == "low"


def test_preset_high_uses_high_alias() -> None:
    profile = resolve_profile(preset="high")
    assert profile.model == DEFAULT_MODEL_HIGH
    assert profile.effort == "max"
    assert profile.preset == "high"


def test_default_aliases_are_three_distinct_skus() -> None:
    from agyloop.domain.model_profile import DEFAULT_MODEL_MEDIUM

    assert len({DEFAULT_MODEL_LOW, DEFAULT_MODEL_MEDIUM, DEFAULT_MODEL_HIGH}) == 3
    assert DEFAULT_MODEL_LOW == "gemini-flash-lite-latest"
    assert DEFAULT_MODEL_MEDIUM == "gemini-2.5-flash"
    assert DEFAULT_MODEL_HIGH == "gemini-2.5-pro"


def test_model_alias_and_effort_override_preset() -> None:
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    profile = resolve_profile(preset="medium", model="high", effort="xhigh", aliases=aliases)
    assert profile.model == "g-high"
    assert profile.effort == "xhigh"
    assert profile.preset == "high"


def test_raw_model_id() -> None:
    profile = resolve_profile(model="gemini-2.0-flash", effort="low")
    assert profile.model == "gemini-2.0-flash"
    assert profile.effort == "low"
    assert profile.preset is None


def test_alias_overrides() -> None:
    aliases = ModelAliases(low="custom-low", medium="custom-med", high="custom-high")
    assert resolve_profile(preset="low", aliases=aliases).model == "custom-low"
    assert resolve_profile(model="medium", aliases=aliases).model == "custom-med"


def test_escalate_and_downgrade_steps() -> None:
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    low = profile_for_preset("low", aliases)
    med = escalate_profile(low, aliases)
    assert med == profile_for_preset("medium", aliases)
    high = escalate_profile(med, aliases)
    assert high.model == "g-high"
    at_max = ModelEffortProfile(model="g-high", effort="max", preset="high")
    assert escalate_profile(at_max, aliases) == at_max
    assert downgrade_profile(high, aliases) == profile_for_preset("medium", aliases)


def test_auto_escalate_stuck_and_operator_lock() -> None:
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    current = profile_for_preset("low", aliases)
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
        aliases=aliases,
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
        aliases=aliases,
    )
    assert locked.profile is None


def test_auto_downgrade_budget_and_progress() -> None:
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    high = profile_for_preset("high", aliases)
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
        aliases=aliases,
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
        aliases=aliases,
    )
    assert progress.reason == "downgrade_progress"
    assert progress.profile == profile_for_preset("medium", aliases)


def test_escalate_outranks_downgrade() -> None:
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    mid = profile_for_preset("medium", aliases)
    decision = decide_auto_model(
        mid,
        consecutive_no_progress=2,
        consecutive_progress=2,
        blocked=False,
        dollars_spent=9.0,
        max_dollars=10.0,
        budget_downgrade_done=False,
        operator_locked=False,
        auto_enabled=True,
        aliases=aliases,
    )
    assert decision.reason == "escalate_stuck"


def test_truncate_chatter() -> None:
    small = truncate_chatter("hi")
    assert small.truncated is False
    big = truncate_chatter("x" * 300_000, cap_bytes=100)
    assert big.truncated is True
    assert len(big.text.encode("utf-8")) <= 100
    mid = truncate_chatter("€", cap_bytes=2)
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
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    high_effort_low = ModelEffortProfile(model=aliases.low, effort="high", preset="low")
    down = downgrade_profile(high_effort_low, aliases)
    assert down.preset == "low"
    assert down.effort == "medium"


def test_escalate_effort_at_high() -> None:
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
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
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    assert downgrade_profile(profile_for_preset("medium", aliases), aliases) == profile_for_preset(
        "low", aliases
    )


def test_resolve_model_ref_none() -> None:
    assert resolve_model_ref(None, ModelAliases()) == DEFAULT_MODEL_LOW


def test_downgrade_custom_model_effort() -> None:
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    custom = ModelEffortProfile(model="gemini-flash-lite", effort="high", preset=None)
    down = downgrade_profile(custom, aliases)
    assert down.model == "gemini-flash-lite"
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
    aliases = ModelAliases(low="g-low", medium="g-med", high="g-high")
    custom = ModelEffortProfile(model="gemini-flash-lite", effort="medium", preset=None)
    down = downgrade_profile(custom, aliases)
    assert down == profile_for_preset("low", aliases)


def test_preset_for_model_high_when_distinct() -> None:
    aliases = ModelAliases(low="a", medium="b", high="c")
    assert aliases.preset_for_model("c") == "high"
    assert aliases.preset_for_model("unknown") is None
    assert aliases.resolve_alias("nope") is None

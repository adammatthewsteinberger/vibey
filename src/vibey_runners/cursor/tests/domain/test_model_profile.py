# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from cursorloop.domain.model_profile import (
    SHIPPED_PRESETS,
    ModelProfile,
    downgrade_profile,
    escalate_profile,
)


def test_default_preset_is_composer() -> None:
    assert SHIPPED_PRESETS["composer"].model_id == "composer-2.5"


def test_grok_is_a_profile_not_a_product() -> None:
    """Grok is one entry in the profile table, reachable through the same
    gateway and the same taxonomy as Composer. There is no separate adapter."""
    grok = SHIPPED_PRESETS["grok"]
    assert grok.model_id == "cursor-grok-4.6"
    assert grok.effort == "high"


def test_fast_variants_are_expressed_as_params_not_ids() -> None:
    profile = SHIPPED_PRESETS["composer-fast"]
    assert profile.model_id == "composer-2.5"
    assert ("fast", "true") in profile.params


def test_router_presets_always_pass_optimize_for_explicitly() -> None:
    """Omitting optimize_for, or sending a legacy 'default', is not a supported
    Router contract."""
    for name in ("router-cost", "router-balanced", "router-intelligence"):
        profile = SHIPPED_PRESETS[name]
        assert profile.model_id == "auto-smart"
        assert any(pid == "optimize_for" for pid, _ in profile.params)


def test_profile_to_selection_payload_is_serialisable() -> None:
    payload = ModelProfile("composer-2.5", params=(("fast", "true"),)).to_selection_payload()
    assert payload == {"id": "composer-2.5", "params": [{"id": "fast", "value": "true"}]}


def test_shipped_presets_cover_the_named_table() -> None:
    assert set(SHIPPED_PRESETS) == {
        "composer",
        "composer-fast",
        "grok",
        "grok-xhigh",
        "grok-4.5",
        "router-cost",
        "router-balanced",
        "router-intelligence",
    }


def test_grok_xhigh_and_4_5_are_profiles_on_the_same_gateway() -> None:
    xhigh = SHIPPED_PRESETS["grok-xhigh"]
    assert xhigh.model_id == "cursor-grok-4.6"
    assert xhigh.effort == "xhigh"
    older = SHIPPED_PRESETS["grok-4.5"]
    assert older.model_id == "cursor-grok-4.5"


def test_router_optimize_for_values_are_the_supported_contract() -> None:
    values = {
        dict(SHIPPED_PRESETS[name].params)["optimize_for"]
        for name in ("router-cost", "router-balanced", "router-intelligence")
    }
    assert values == {"cost", "balanced", "intelligence"}
    for name in ("router-cost", "router-balanced", "router-intelligence"):
        assert "default" not in dict(SHIPPED_PRESETS[name].params).values()


def test_plain_composer_payload_omits_empty_params() -> None:
    assert SHIPPED_PRESETS["composer"].to_selection_payload() == {"id": "composer-2.5"}


def test_effort_is_emitted_on_the_wire_when_set() -> None:
    payload = SHIPPED_PRESETS["grok"].to_selection_payload()
    assert payload["id"] == "cursor-grok-4.6"
    assert {"id": "effort", "value": "high"} in payload["params"]  # type: ignore[operator]


def test_fast_field_is_synthesised_into_params_when_missing() -> None:
    payload = ModelProfile("composer-2.5", fast=True).to_selection_payload()
    assert payload == {"id": "composer-2.5", "params": [{"id": "fast", "value": "true"}]}


def test_escalate_steps_up_the_preset_ladder() -> None:
    fast = SHIPPED_PRESETS["composer-fast"]
    composer = escalate_profile(fast)
    assert composer == SHIPPED_PRESETS["composer"]
    grok45 = escalate_profile(composer)
    assert grok45 == SHIPPED_PRESETS["grok-4.5"]
    grok = escalate_profile(grok45)
    assert grok == SHIPPED_PRESETS["grok"]
    xhigh = escalate_profile(grok)
    assert xhigh == SHIPPED_PRESETS["grok-xhigh"]
    assert escalate_profile(xhigh) == xhigh


def test_downgrade_steps_down_the_preset_ladder() -> None:
    xhigh = SHIPPED_PRESETS["grok-xhigh"]
    grok = downgrade_profile(xhigh)
    assert grok == SHIPPED_PRESETS["grok"]
    grok45 = downgrade_profile(grok)
    assert grok45 == SHIPPED_PRESETS["grok-4.5"]
    composer = downgrade_profile(grok45)
    assert composer == SHIPPED_PRESETS["composer"]
    fast = downgrade_profile(composer)
    assert fast == SHIPPED_PRESETS["composer-fast"]
    assert downgrade_profile(fast) == fast


def test_router_escalates_and_downgrades_on_its_own_ladder() -> None:
    cost = SHIPPED_PRESETS["router-cost"]
    balanced = escalate_profile(cost)
    assert balanced == SHIPPED_PRESETS["router-balanced"]
    intel = escalate_profile(balanced)
    assert intel == SHIPPED_PRESETS["router-intelligence"]
    assert escalate_profile(intel) == intel
    assert downgrade_profile(intel) == balanced
    assert downgrade_profile(cost) == cost


def test_unmatched_profile_escalates_to_ceiling_and_downgrades_to_floor() -> None:
    custom = ModelProfile("some-future-model")
    assert escalate_profile(custom) == SHIPPED_PRESETS["grok-xhigh"]
    assert downgrade_profile(custom) == SHIPPED_PRESETS["composer"]

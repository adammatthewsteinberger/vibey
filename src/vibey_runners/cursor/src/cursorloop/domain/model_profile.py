# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Composer-first model profiles. Grok is a profile, not a product.

``to_selection_payload`` is a plain dict so ``domain/`` never imports
``cursor_sdk``. The gateway maps it onto ``ModelSelection``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_PRESET_LADDER: tuple[str, ...] = (
    "composer-fast",
    "composer",
    "grok-4.5",
    "grok",
    "grok-xhigh",
)
_ROUTER_LADDER: tuple[str, ...] = (
    "router-cost",
    "router-balanced",
    "router-intelligence",
)


@dataclass(frozen=True, slots=True)
class ModelProfile:
    model_id: str
    params: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    effort: str | None = None
    fast: bool = False

    def to_selection_payload(self) -> dict[str, object]:
        items: list[dict[str, str]] = [{"id": pid, "value": val} for pid, val in self.params]
        seen = {item["id"] for item in items}
        if self.fast and "fast" not in seen:
            items.append({"id": "fast", "value": "true"})
        if self.effort is not None and "effort" not in seen:
            items.append({"id": "effort", "value": self.effort})
        payload: dict[str, object] = {"id": self.model_id}
        if items:
            payload["params"] = items
        return payload


def _p(
    model_id: str,
    *,
    params: tuple[tuple[str, str], ...] = (),
    effort: str | None = None,
    fast: bool = False,
) -> ModelProfile:
    return ModelProfile(model_id, params=params, effort=effort, fast=fast)


SHIPPED_PRESETS: dict[str, ModelProfile] = {
    "composer": _p("composer-2.5"),
    "composer-fast": _p("composer-2.5", params=(("fast", "true"),), fast=True),
    "grok": _p("cursor-grok-4.6", effort="high"),
    "grok-xhigh": _p("cursor-grok-4.6", effort="xhigh"),
    "grok-4.5": _p("cursor-grok-4.5", effort="high"),
    "router-cost": _p("auto-smart", params=(("optimize_for", "cost"),)),
    "router-balanced": _p("auto-smart", params=(("optimize_for", "balanced"),)),
    "router-intelligence": _p("auto-smart", params=(("optimize_for", "intelligence"),)),
}

DEFAULT_PRESET = "composer"


def _ladder_for(profile: ModelProfile) -> tuple[str, ...]:
    if profile.model_id == "auto-smart":
        return _ROUTER_LADDER
    return _PRESET_LADDER


def _index_on_ladder(profile: ModelProfile, ladder: tuple[str, ...]) -> int | None:
    for index, name in enumerate(ladder):
        if SHIPPED_PRESETS[name] == profile:
            return index
    return None


def floor_profile(current: ModelProfile) -> ModelProfile:
    """Cheap workhorse for this ladder. Budget force-to-low lands here.

    ``composer-fast`` is a speed variant below the default, not the budget floor.
    """
    ladder = _ladder_for(current)
    if ladder is _ROUTER_LADDER:
        return SHIPPED_PRESETS["router-cost"]
    return SHIPPED_PRESETS["composer"]


def escalate_profile(current: ModelProfile) -> ModelProfile:
    """Move one step up the shipped ladder; unmatched ids jump to grok-xhigh."""
    ladder = _ladder_for(current)
    index = _index_on_ladder(current, ladder)
    if index is None:
        return SHIPPED_PRESETS["grok-xhigh"]
    if index >= len(ladder) - 1:
        return current
    return SHIPPED_PRESETS[ladder[index + 1]]


def downgrade_profile(current: ModelProfile) -> ModelProfile:
    """Move one step down the shipped ladder; unmatched ids drop to composer."""
    ladder = _ladder_for(current)
    index = _index_on_ladder(current, ladder)
    if index is None:
        return SHIPPED_PRESETS["composer"]
    if index <= 0:
        return current
    return SHIPPED_PRESETS[ladder[index - 1]]

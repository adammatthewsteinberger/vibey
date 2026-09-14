# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Model + effort profile resolution — pure, no I/O.

Preset tiers map through configurable aliases named ``low`` / ``medium`` /
``high`` to concrete Anthropic model ids."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EffortLevel = Literal["low", "medium", "high", "xhigh", "max"]
PresetName = Literal["low", "medium", "high"]

EFFORT_LEVELS: tuple[EffortLevel, ...] = ("low", "medium", "high", "xhigh", "max")
PRESET_NAMES: tuple[PresetName, ...] = ("low", "medium", "high")

DEFAULT_MODEL_LOW = "claude-sonnet-4-5"
DEFAULT_MODEL_MEDIUM = "claude-opus-4-6"
DEFAULT_MODEL_HIGH = "claude-fable-5"

PRESET_DEFAULT_EFFORT: dict[PresetName, EffortLevel] = {
    "low": "medium",
    "medium": "high",
    "high": "max",
}


@dataclass(frozen=True, slots=True)
class ModelAliases:
    low: str = DEFAULT_MODEL_LOW
    medium: str = DEFAULT_MODEL_MEDIUM
    high: str = DEFAULT_MODEL_HIGH

    def resolve_alias(self, name: str) -> str | None:
        key = name.strip().lower()
        if key == "low":
            return self.low
        if key == "medium":
            return self.medium
        if key == "high":
            return self.high
        return None

    def preset_for_model(self, model: str) -> PresetName | None:
        if model == self.low:
            return "low"
        if model == self.medium:
            return "medium"
        if model == self.high:
            return "high"
        return None


@dataclass(frozen=True, slots=True)
class ModelEffortProfile:
    model: str
    effort: EffortLevel
    preset: PresetName | None = None


def parse_effort(value: str) -> EffortLevel:
    key = value.strip().lower()
    if key not in EFFORT_LEVELS:
        raise ValueError(f"invalid effort {value!r}; expected one of {EFFORT_LEVELS}")
    return key


def parse_preset(value: str) -> PresetName:
    key = value.strip().lower()
    if key not in PRESET_NAMES:
        raise ValueError(f"invalid preset {value!r}; expected one of {PRESET_NAMES}")
    return key


def profile_for_preset(preset: PresetName, aliases: ModelAliases) -> ModelEffortProfile:
    model = aliases.resolve_alias(preset)
    # Precondition, not a security gate: PresetName is the closed union
    # {low, medium, high} and resolve_alias handles every member, so this
    # is exhaustive by construction — asserted here to fail loudly if a
    # future preset is added without a matching alias branch.
    assert model is not None  # nosec B101
    return ModelEffortProfile(
        model=model,
        effort=PRESET_DEFAULT_EFFORT[preset],
        preset=preset,
    )


def resolve_model_ref(model: str | None, aliases: ModelAliases) -> str:
    if model is None or not model.strip():
        return aliases.low
    aliased = aliases.resolve_alias(model)
    return aliased if aliased is not None else model.strip()


def resolve_profile(
    *,
    preset: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    aliases: ModelAliases | None = None,
) -> ModelEffortProfile:
    """Resolve CLI/config inputs to a concrete profile.

    Preset sets model+effort first; ``--model`` / ``--effort`` then override
    individually. Unset model defaults to alias ``low``; unset effort defaults
    to ``medium`` (or the preset's effort when a preset was applied).
    """
    table = aliases or ModelAliases()
    applied_preset: PresetName | None = None
    resolved_model = table.low
    resolved_effort: EffortLevel = "medium"

    if preset is not None and str(preset).strip():
        applied_preset = parse_preset(str(preset))
        base = profile_for_preset(applied_preset, table)
        resolved_model = base.model
        resolved_effort = base.effort

    if model is not None and str(model).strip():
        resolved_model = resolve_model_ref(str(model), table)
        # Raw model override clears preset tag unless it still matches an alias.
        applied_preset = table.preset_for_model(resolved_model)

    if effort is not None and str(effort).strip():
        resolved_effort = parse_effort(str(effort))

    if applied_preset is None:
        applied_preset = table.preset_for_model(resolved_model)

    return ModelEffortProfile(
        model=resolved_model,
        effort=resolved_effort,
        preset=applied_preset,
    )


def escalate_profile(current: ModelEffortProfile, aliases: ModelAliases) -> ModelEffortProfile:
    """Move one step up: low→medium→high preset, then effort toward max."""
    preset = current.preset or aliases.preset_for_model(current.model)
    if preset == "low":
        return profile_for_preset("medium", aliases)
    if preset == "medium":
        return profile_for_preset("high", aliases)
    # high or custom: bump effort
    idx = EFFORT_LEVELS.index(current.effort)
    if idx >= len(EFFORT_LEVELS) - 1:
        return current
    return ModelEffortProfile(
        model=current.model if preset == "high" else aliases.high,
        effort=EFFORT_LEVELS[idx + 1],
        preset="high" if preset == "high" else current.preset,
    )


def downgrade_profile(current: ModelEffortProfile, aliases: ModelAliases) -> ModelEffortProfile:
    """Move one step down: high→medium→low preset; at low, effort floor is medium."""
    preset = current.preset or aliases.preset_for_model(current.model)
    if preset == "high":
        return profile_for_preset("medium", aliases)
    if preset == "medium":
        return profile_for_preset("low", aliases)
    # low or custom: lower effort but not below medium for low preset
    idx = EFFORT_LEVELS.index(current.effort)
    floor_idx = EFFORT_LEVELS.index("medium")
    if idx <= floor_idx:
        return profile_for_preset("low", aliases)
    return ModelEffortProfile(
        model=aliases.low if preset == "low" else current.model,
        effort=EFFORT_LEVELS[idx - 1],
        preset="low" if preset == "low" else current.preset,
    )

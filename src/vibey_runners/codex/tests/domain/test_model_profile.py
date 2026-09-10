# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Model + effort profiles with low/medium/high presets."""

from __future__ import annotations

from codexloop.domain.model_profile import Effort, ModelEffortProfile


def test_presets_low_medium_high() -> None:
    assert ModelEffortProfile.low("gpt-5") == ModelEffortProfile(model="gpt-5", effort=Effort.LOW)
    assert ModelEffortProfile.medium("gpt-5") == ModelEffortProfile(
        model="gpt-5", effort=Effort.MEDIUM
    )
    assert ModelEffortProfile.high("o3") == ModelEffortProfile(model="o3", effort=Effort.HIGH)


def test_effort_values_are_codex_strings() -> None:
    assert Effort.LOW == "low"
    assert Effort.MEDIUM == "medium"
    assert Effort.HIGH == "high"
    assert Effort.LOW.value == "low"


def test_profile_is_frozen_slots_value() -> None:
    profile = ModelEffortProfile.medium("gpt-5")
    assert profile.__dataclass_params__.frozen is True
    assert profile.__dataclass_params__.slots is True
    assert hash(profile) == hash(profile)

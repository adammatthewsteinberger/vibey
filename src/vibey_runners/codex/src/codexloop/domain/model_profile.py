# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Model + reasoning-effort profile with low/medium/high presets."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Effort(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ModelEffortProfile:
    model: str
    effort: Effort

    @classmethod
    def low(cls, model: str) -> ModelEffortProfile:
        return cls(model=model, effort=Effort.LOW)

    @classmethod
    def medium(cls, model: str) -> ModelEffortProfile:
        return cls(model=model, effort=Effort.MEDIUM)

    @classmethod
    def high(cls, model: str) -> ModelEffortProfile:
        return cls(model=model, effort=Effort.HIGH)

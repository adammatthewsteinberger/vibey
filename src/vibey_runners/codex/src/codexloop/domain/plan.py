# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Markdown work-plan parsing. Checkboxes are the load-bearing items."""

from __future__ import annotations

import re
from dataclasses import dataclass

from codexloop.domain.errors import ConfigurationError

_CHECKBOX = re.compile(r"^[ \t]*[-*+][ \t]+\[([ xX])\][ \t]+(\S.*)$")


@dataclass(frozen=True, slots=True)
class PlanItem:
    name: str
    done: bool


@dataclass(frozen=True, slots=True)
class WorkPlan:
    items: tuple[PlanItem, ...]

    @classmethod
    def parse(cls, text: str) -> WorkPlan:
        items: list[PlanItem] = []
        for line in text.splitlines():
            matched = _CHECKBOX.match(line.rstrip())
            if matched is None:
                continue
            marker, name = matched.group(1), matched.group(2).strip()
            items.append(PlanItem(name=name, done=marker in "xX"))
        if not items:
            raise ConfigurationError("work plan has no checkbox items")
        return cls(items=tuple(items))

    @property
    def remaining_work(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.items if not item.done)

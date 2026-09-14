# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Work plan value objects — parsing a handoff markdown file into discrete items."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from claudeloop.domain.errors import InvalidPlanError

_CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s*(.+?)\s*$")


@dataclass(frozen=True, slots=True)
class PlanItem:
    """One unit of work parsed from a plan file's checkbox list."""

    text: str
    done: bool = False

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise InvalidPlanError("Plan item text must not be blank")


@dataclass(frozen=True, slots=True)
class WorkPlan:
    """The full body of a handoff plan, plus any checkbox items found in it."""

    raw_text: str
    items: tuple[PlanItem, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.raw_text.strip():
            raise InvalidPlanError("Plan text must not be blank")

    @property
    def has_items(self) -> bool:
        return len(self.items) > 0

    @property
    def remaining_items(self) -> tuple[PlanItem, ...]:
        return tuple(item for item in self.items if not item.done)

    @property
    def is_fully_done(self) -> bool:
        return self.has_items and len(self.remaining_items) == 0

    @staticmethod
    def parse(raw_text: str) -> WorkPlan:
        """Parse a markdown plan. Checkbox lines (`- [ ] ...` / `- [x] ...`) become
        tracked items; a plan with no checkboxes is still valid (bare instructions),
        just with an empty items tuple."""
        if not raw_text.strip():
            raise InvalidPlanError("Plan text must not be blank")

        items: list[PlanItem] = []
        for line in raw_text.splitlines():
            match = _CHECKBOX_RE.match(line)
            if match:
                done = match.group(1).lower() == "x"
                items.append(PlanItem(text=match.group(2), done=done))

        return WorkPlan(raw_text=raw_text, items=tuple(items))

    def with_items_marked_done(self, done_texts: frozenset[str]) -> WorkPlan:
        """Return a new WorkPlan with any item whose text is in `done_texts` marked done.
        Used to reconcile a structured-output verdict's `remaining_work` against the
        plan's own checklist between turns."""
        new_items = tuple(
            item if item.text not in done_texts else PlanItem(text=item.text, done=True)
            for item in self.items
        )
        return WorkPlan(raw_text=self.raw_text, items=new_items)

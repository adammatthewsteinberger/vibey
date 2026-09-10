# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Markdown work-plan parsing: checkboxes are load-bearing PlanItems."""

from __future__ import annotations

import pytest

from codexloop.domain.errors import ConfigurationError
from codexloop.domain.plan import PlanItem, WorkPlan

MARKDOWN_PLAN = """\
# Authentication

Prose that is not an item.

- [ ] Add login
- [x] Add logout

## Billing

* [ ] Charge card
+ [X] Refund path
"""


def test_headings_and_checkboxes_become_plan_items() -> None:
    plan = WorkPlan.parse(MARKDOWN_PLAN)
    assert plan.items == (
        PlanItem(name="Add login", done=False),
        PlanItem(name="Add logout", done=True),
        PlanItem(name="Charge card", done=False),
        PlanItem(name="Refund path", done=True),
    )


def test_empty_plan_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        WorkPlan.parse("")


def test_whitespace_only_plan_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        WorkPlan.parse("  \n\t\n  ")


def test_headings_without_checkboxes_are_empty_and_raise() -> None:
    with pytest.raises(ConfigurationError):
        WorkPlan.parse("# Only a heading\n\nSome prose.\n")


def test_remaining_work_names_round_trip_stably() -> None:
    plan = WorkPlan.parse(MARKDOWN_PLAN)
    remaining = plan.remaining_work
    assert remaining == ("Add login", "Charge card")

    reconstructed = "\n".join(f"- [ ] {name}" for name in remaining)
    again = WorkPlan.parse(reconstructed)
    assert again.remaining_work == remaining
    assert again.remaining_work == ("Add login", "Charge card")
    assert list(again.remaining_work) == ["Add login", "Charge card"]


def test_plan_item_and_work_plan_are_frozen_slots() -> None:
    item = PlanItem(name="task", done=False)
    plan = WorkPlan.parse("- [ ] task\n")
    assert item.__dataclass_params__.frozen is True
    assert item.__dataclass_params__.slots is True
    assert plan.__dataclass_params__.frozen is True
    assert plan.__dataclass_params__.slots is True
    assert hash(item) == hash(item)
    assert hash(plan) == hash(plan)

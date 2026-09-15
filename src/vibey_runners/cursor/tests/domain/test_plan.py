# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import pytest

from cursorloop.domain.completion import Blocked, Continue, Done, reconcile
from cursorloop.domain.errors import PlanParseError
from cursorloop.domain.plan import PlanItem, WorkPlan


def test_plan_item_rejects_blank_text() -> None:
    with pytest.raises(PlanParseError):
        PlanItem(text="   ")


def test_plan_item_defaults_to_not_done() -> None:
    assert PlanItem(text="x").done is False


def test_workplan_rejects_blank_text() -> None:
    with pytest.raises(PlanParseError):
        WorkPlan(raw_text="")


def test_workplan_defaults_to_no_items() -> None:
    plan = WorkPlan(raw_text="bare instructions")
    assert plan.items == ()
    assert plan.has_items is False


def test_parse_rejects_blank_text() -> None:
    with pytest.raises(PlanParseError):
        WorkPlan.parse("   \n  ")


def test_parse_bare_instructions_no_checkboxes() -> None:
    plan = WorkPlan.parse("Just do the thing, no checklist here.")
    assert plan.has_items is False
    assert plan.remaining_items == ()
    assert plan.is_fully_done is False


def test_parse_checkbox_items() -> None:
    text = """
    # Plan
    - [ ] first item
    - [x] second item done
    * [X] third item also done (uppercase X, star bullet)
    not a checkbox line
    """
    plan = WorkPlan.parse(text)
    assert len(plan.items) == 3
    assert plan.items[0] == PlanItem(text="first item", done=False)
    assert plan.items[1] == PlanItem(text="second item done", done=True)
    assert plan.items[2] == PlanItem(
        text="third item also done (uppercase X, star bullet)", done=True
    )
    assert plan.remaining_items == (PlanItem(text="first item", done=False),)
    assert plan.has_items is True
    assert plan.is_fully_done is False


def test_is_fully_done_true_when_all_items_done() -> None:
    plan = WorkPlan.parse("- [x] only item")
    assert plan.is_fully_done is True


def test_with_items_marked_done() -> None:
    plan = WorkPlan.parse("- [ ] a\n- [ ] b")
    updated = plan.with_items_marked_done(frozenset({"a"}))
    assert updated.items[0].done is True
    assert updated.items[1].done is False
    assert plan.items[0].done is False


def test_with_items_marked_done_no_match_is_noop() -> None:
    plan = WorkPlan.parse("- [ ] a")
    updated = plan.with_items_marked_done(frozenset({"nonexistent"}))
    assert updated.items[0].done is False


def test_reconcile_downgrades_done_when_unchecked_items_remain() -> None:
    plan = WorkPlan.parse("- [ ] wire the gateway\n- [x] already shipped")
    assert reconcile(Done(summary="claimed done"), plan) == Continue(
        remaining_work=("wire the gateway",)
    )


def test_reconcile_keeps_done_when_the_plan_is_fully_checked() -> None:
    plan = WorkPlan.parse("- [x] only item")
    verdict = Done(summary="shipped")
    assert reconcile(verdict, plan) is verdict


def test_reconcile_keeps_done_for_bare_instructions() -> None:
    plan = WorkPlan.parse("Just do the thing.")
    verdict = Done()
    assert reconcile(verdict, plan) is verdict


def test_reconcile_never_upgrades_continue_or_blocked() -> None:
    plan = WorkPlan.parse("- [x] only item")
    continuing = Continue(remaining_work=("more",))
    blocked = Blocked(reason="needs credentials")
    assert reconcile(continuing, plan) is continuing
    assert reconcile(blocked, plan) is blocked

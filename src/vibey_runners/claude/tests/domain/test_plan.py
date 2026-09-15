# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from claudeloop.domain.errors import InvalidPlanError
from claudeloop.domain.plan import PlanItem, WorkPlan


def test_plan_item_rejects_blank_text():
    with pytest.raises(InvalidPlanError):
        PlanItem(text="   ")


def test_workplan_rejects_blank_text():
    with pytest.raises(InvalidPlanError):
        WorkPlan(raw_text="")


def test_parse_rejects_blank_text():
    with pytest.raises(InvalidPlanError):
        WorkPlan.parse("   \n  ")


def test_parse_bare_instructions_no_checkboxes():
    plan = WorkPlan.parse("Just do the thing, no checklist here.")
    assert plan.has_items is False
    assert plan.remaining_items == ()
    assert plan.is_fully_done is False


def test_parse_checkbox_items():
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


def test_is_fully_done_true_when_all_items_done():
    plan = WorkPlan.parse("- [x] only item")
    assert plan.is_fully_done is True


def test_with_items_marked_done():
    plan = WorkPlan.parse("- [ ] a\n- [ ] b")
    updated = plan.with_items_marked_done(frozenset({"a"}))
    assert updated.items[0].done is True
    assert updated.items[1].done is False
    # original untouched (immutability)
    assert plan.items[0].done is False


def test_with_items_marked_done_no_match_is_noop():
    plan = WorkPlan.parse("- [ ] a")
    updated = plan.with_items_marked_done(frozenset({"nonexistent"}))
    assert updated.items[0].done is False

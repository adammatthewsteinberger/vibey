# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from claudeloop.domain.errors import InvalidSessionSelectorError
from claudeloop.domain.session import (
    ExplicitSessionSelector,
    MostRecentSessionSelector,
    PlanFileSelector,
    SessionRef,
)


def test_session_ref_valid():
    ref = SessionRef(session_id="abc", cwd="/repo")
    assert ref.session_id == "abc"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"session_id": "", "cwd": "/repo"},
        {"session_id": "abc", "cwd": ""},
        {"session_id": "  ", "cwd": "/repo"},
    ],
)
def test_session_ref_rejects_blank_fields(kwargs):
    with pytest.raises(InvalidSessionSelectorError):
        SessionRef(**kwargs)


def test_plan_file_selector_rejects_blank():
    with pytest.raises(InvalidSessionSelectorError):
        PlanFileSelector(plan_path="")


def test_explicit_session_selector_rejects_blank():
    with pytest.raises(InvalidSessionSelectorError):
        ExplicitSessionSelector(session_id="")


def test_most_recent_selector_rejects_blank():
    with pytest.raises(InvalidSessionSelectorError):
        MostRecentSessionSelector(cwd="")


def test_selectors_valid_construction():
    assert PlanFileSelector(plan_path="handoff.md").plan_path == "handoff.md"
    assert ExplicitSessionSelector(session_id="sid").session_id == "sid"
    assert MostRecentSessionSelector(cwd="/repo").cwd == "/repo"

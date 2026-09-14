# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cursorloop.domain.session import (
    AgentRef,
    ExplicitAgentSelector,
    InvalidAgentSelectorError,
    MostRecentAgentSelector,
    PlanFileSelector,
    runtime_from_id,
)


def test_runtime_from_id_maps_bc_prefix_to_cloud() -> None:
    assert runtime_from_id("bc-abc123") == "cloud"
    assert runtime_from_id("agent-local-1") == "local"
    assert runtime_from_id("bc") == "local"


def test_agent_ref_valid() -> None:
    modified = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    ref = AgentRef(
        agent_id="bc-abc",
        runtime="cloud",
        cwd="/repo",
        name="demo",
        summary="working",
        last_modified=modified,
        status="running",
    )
    assert ref.agent_id == "bc-abc"
    assert ref.runtime == "cloud"
    assert ref.cwd == "/repo"
    assert ref.name == "demo"
    assert ref.summary == "working"
    assert ref.last_modified == modified
    assert ref.status == "running"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"agent_id": "", "runtime": "local", "cwd": "/repo"},
        {"agent_id": "abc", "runtime": "local", "cwd": ""},
        {"agent_id": "  ", "runtime": "local", "cwd": "/repo"},
        {"agent_id": "abc", "runtime": "local", "cwd": "  "},
    ],
)
def test_agent_ref_rejects_blank_fields(kwargs: dict[str, str]) -> None:
    with pytest.raises(InvalidAgentSelectorError):
        AgentRef(**kwargs)


def test_plan_file_selector_rejects_blank() -> None:
    with pytest.raises(InvalidAgentSelectorError):
        PlanFileSelector(plan_path="")


def test_explicit_agent_selector_rejects_blank() -> None:
    with pytest.raises(InvalidAgentSelectorError):
        ExplicitAgentSelector(agent_id="")


def test_most_recent_selector_rejects_blank() -> None:
    with pytest.raises(InvalidAgentSelectorError):
        MostRecentAgentSelector(cwd="")


def test_selectors_valid_construction() -> None:
    assert PlanFileSelector(plan_path="handoff.md").plan_path == "handoff.md"
    assert ExplicitAgentSelector(agent_id="sid").agent_id == "sid"
    assert MostRecentAgentSelector(cwd="/repo").cwd == "/repo"

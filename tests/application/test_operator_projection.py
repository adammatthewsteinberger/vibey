# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The operator's decisions, tested without a cluster.

That is the whole point of keeping this module pure: whether a project is
Ready, what reason a park reports, and which answers may be applied are
the parts that must be right, and none of them need Kubernetes to check.
"""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from vibey.application.dto import HumanGateRecord, ProjectRecord
from vibey.application.operator_projection import (
    MAX_MESSAGE,
    plan_answers,
    project_conditions,
    project_status,
    reason_for_kind,
)
from vibey.domain.phase import Phase


def _project(phase: Phase = Phase.BUILD, cycle: int = 1) -> ProjectRecord:
    now = datetime.now(UTC)
    return ProjectRecord(
        project_id=uuid4(),
        name="demo",
        repo_path=Path("/work/demo"),
        phase=phase,
        cycle=cycle,
        max_cycles=3,
        config={},
        created_at=now,
        updated_at=now,
    )


def _gate(kind: str = "question", prompt: str = "which shape?") -> HumanGateRecord:
    return HumanGateRecord(
        gate_id=uuid4(),
        project_id=uuid4(),
        job_id=uuid4(),
        kind=kind,
        prompt=prompt,
        options=(),
        default_answer=None,
        answer=None,
        raised_at=datetime.now(UTC),
        timeout_at=None,
        answered_at=None,
        answered_by=None,
    )


def _by_type(conditions: tuple[object, ...]) -> dict[str, object]:
    return {c.type: c for c in conditions}  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("budget_exhausted", "BudgetExhausted"),
        ("question", "Question"),
        ("deploy_failure_triage", "DeployFailureTriage"),
        ("too-many-wind-downs", "TooManyWindDowns"),
        ("___", "Unknown"),
    ],
)
def test_gate_kinds_become_camelcase_kubernetes_reasons(kind: str, expected: str) -> None:
    """Kubernetes reasons are CamelCase tokens. A raw `budget_exhausted`
    is not one, and tooling filtering on reason would silently miss it."""
    assert reason_for_kind(kind) == expected


def test_a_progressing_project_is_ready_and_not_parked() -> None:
    conditions = _by_type(project_conditions(_project(), []))
    assert conditions["Ready"].status == "True"  # type: ignore[attr-defined]
    assert conditions["Ready"].reason == "Progressing"  # type: ignore[attr-defined]
    assert conditions["Parked"].status == "False"  # type: ignore[attr-defined]
    assert conditions["Complete"].status == "False"  # type: ignore[attr-defined]


def test_an_open_gate_makes_the_project_parked_and_not_ready() -> None:
    conditions = _by_type(
        project_conditions(_project(), [_gate("budget_exhausted", "grant more?")])
    )
    assert conditions["Parked"].status == "True"  # type: ignore[attr-defined]
    assert conditions["Parked"].reason == "BudgetExhausted"  # type: ignore[attr-defined]
    assert "grant more?" in conditions["Parked"].message  # type: ignore[attr-defined]
    assert conditions["Ready"].status == "False"  # type: ignore[attr-defined]
    assert conditions["Ready"].reason == "AwaitingHuman"  # type: ignore[attr-defined]


def test_several_open_gates_are_counted_not_hidden() -> None:
    """Reporting only the first would make answering it look like progress
    when the project is still parked on two more."""
    conditions = _by_type(project_conditions(_project(), [_gate(), _gate(), _gate()]))
    assert "+2 more" in conditions["Parked"].message  # type: ignore[attr-defined]
    assert "3 gate(s)" in conditions["Ready"].message  # type: ignore[attr-defined]


def test_a_done_project_is_complete_and_not_ready() -> None:
    conditions = _by_type(project_conditions(_project(phase=Phase.DONE), []))
    assert conditions["Complete"].status == "True"  # type: ignore[attr-defined]
    assert conditions["Ready"].status == "False"  # type: ignore[attr-defined]
    assert conditions["Ready"].reason == "Complete"  # type: ignore[attr-defined]


def test_an_abandoned_project_is_not_ready_and_says_why() -> None:
    conditions = _by_type(project_conditions(_project(phase=Phase.ABANDONED), []))
    assert conditions["Ready"].status == "False"  # type: ignore[attr-defined]
    assert conditions["Ready"].reason == "Abandoned"  # type: ignore[attr-defined]


def test_a_long_prompt_is_truncated_for_etcd() -> None:
    conditions = _by_type(project_conditions(_project(), [_gate(prompt="x" * 5000)]))
    message = conditions["Parked"].message  # type: ignore[attr-defined]
    assert len(message) == MAX_MESSAGE
    assert message.endswith("…")


def test_status_carries_the_ids_a_human_needs_to_act() -> None:
    project = _project()
    gate = _gate()
    status = project_status(project, [gate])
    assert status["projectId"] == str(project.project_id)
    assert status["phase"] == "build"
    assert status["openGates"] == [
        {"gateId": str(gate.gate_id), "kind": "question", "prompt": "which shape?"}
    ]
    assert len(status["conditions"]) == 3  # type: ignore[arg-type]


def test_answers_are_applied_only_to_gates_that_are_actually_open() -> None:
    open_gate = _gate()
    plan = plan_answers({str(open_gate.gate_id): {"choice": "yes"}}, [open_gate])
    assert plan.apply == ((open_gate.gate_id, {"choice": "yes"}),)
    assert plan.ignored == ()


def test_an_answer_for_an_already_closed_gate_is_ignored_not_attempted() -> None:
    """A CR is declarative and will still name yesterday's gate tomorrow.
    That is a no-op, not an error worth escalating."""
    stale = uuid4()
    plan = plan_answers({str(stale): {"choice": "yes"}}, [])
    assert plan.apply == ()
    assert plan.ignored == ((str(stale), "no open gate with that id"),)


def test_a_key_that_is_not_a_gate_id_is_reported_rather_than_dropped() -> None:
    """A second write path that silently ignores input is how an operator
    appears to work while doing nothing."""
    plan = plan_answers({"not-a-uuid": {"choice": "yes"}}, [])
    assert plan.ignored == (("not-a-uuid", "not a gate id"),)


def test_a_non_object_answer_is_reported() -> None:
    gate = _gate()
    plan = plan_answers({str(gate.gate_id): "just a string"}, [gate])
    assert plan.apply == ()
    assert plan.ignored == ((str(gate.gate_id), "answer must be an object"),)


def test_plan_is_empty_for_an_empty_spec() -> None:
    assert plan_answers({}, [_gate()]) == plan_answers({}, [])


def test_uuid_keys_are_matched_case_and_format_insensitively() -> None:
    """kubectl users type gate ids by hand; a hyphenless or upper-cased
    id is the same gate."""
    gate = _gate()
    hyphenless = gate.gate_id.hex.upper()
    plan = plan_answers({hyphenless: {"choice": "y"}}, [gate])
    assert plan.apply == ((UUID(hyphenless), {"choice": "y"}),)

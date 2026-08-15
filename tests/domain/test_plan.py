from vibey.domain.effort import Effort
from vibey.domain.plan import VerificationSpec, WorkItem, validate_decomposition


def _item(item_id: str, **overrides: object) -> WorkItem:
    defaults: dict[str, object] = {
        "item_id": item_id,
        "title": f"do {item_id}",
        "acceptance_ids": (),
        "depends_on": (),
        "est_effort": Effort.LOW,
        "files_touched_hint": (),
        "verification": VerificationSpec(commands=("pytest",), criteria_checked=("AC-1",)),
    }
    defaults.update(overrides)
    return WorkItem(**defaults)  # type: ignore[arg-type]


def test_validate_decomposition_empty_when_all_rules_pass() -> None:
    items = [
        _item("skeleton", acceptance_ids=("AC-1",)),
        _item("item-2", acceptance_ids=("AC-2",), depends_on=("skeleton",)),
    ]
    violations = validate_decomposition(
        items, criteria_ids=("AC-1", "AC-2"), walking_skeleton_item_id="skeleton"
    )
    assert violations == ()


def test_validate_decomposition_flags_unmapped_criteria() -> None:
    items = [_item("skeleton", acceptance_ids=("AC-1",))]
    violations = validate_decomposition(
        items, criteria_ids=("AC-1", "AC-2"), walking_skeleton_item_id="skeleton"
    )
    assert any("AC-2" in v and "unmapped" in v for v in violations)


def test_validate_decomposition_flags_walking_skeleton_with_dependencies() -> None:
    items = [
        _item("dep", acceptance_ids=("AC-1",)),
        _item("skeleton", acceptance_ids=("AC-2",), depends_on=("dep",)),
    ]
    violations = validate_decomposition(
        items, criteria_ids=("AC-1", "AC-2"), walking_skeleton_item_id="skeleton"
    )
    assert any("no dependencies" in v for v in violations)


def test_validate_decomposition_flags_missing_walking_skeleton() -> None:
    items = [_item("item-1", acceptance_ids=("AC-1",))]
    violations = validate_decomposition(
        items, criteria_ids=("AC-1",), walking_skeleton_item_id="skeleton"
    )
    assert any("not found" in v for v in violations)


def test_validate_decomposition_flags_duplicate_item_ids() -> None:
    items = [_item("skeleton", acceptance_ids=("AC-1",)), _item("skeleton", acceptance_ids=())]
    violations = validate_decomposition(
        items, criteria_ids=("AC-1",), walking_skeleton_item_id="skeleton"
    )
    assert any("duplicate" in v and "skeleton" in v for v in violations)


def test_validate_decomposition_flags_dependency_on_unknown_item() -> None:
    items = [_item("skeleton", acceptance_ids=("AC-1",), depends_on=("ghost",))]
    violations = validate_decomposition(
        items, criteria_ids=("AC-1",), walking_skeleton_item_id="skeleton"
    )
    assert any("ghost" in v and "unknown item" in v for v in violations)


def test_validate_decomposition_reports_every_violation_at_once() -> None:
    items = [_item("skeleton", acceptance_ids=(), depends_on=("ghost",))]
    violations = validate_decomposition(
        items, criteria_ids=("AC-1",), walking_skeleton_item_id="skeleton"
    )
    assert len(violations) >= 2

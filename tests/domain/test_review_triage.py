# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from vibey.domain.effort import Effort, triage_required_effort
from vibey.domain.projections import DecisionLogEntry
from vibey.domain.review import (
    Ambiguity,
    FindingRef,
    Severity,
    check_clear_conditions,
    classify_finding_severity,
    triage_finding,
)
from vibey.domain.spec import AcceptanceCriterion, DesignSpec


def _make_spec() -> DesignSpec:
    return DesignSpec(
        objective="Notes application",
        constraints=("python 3.12+",),
        non_goals=("multi-tenant cloud",),
        criteria=(
            AcceptanceCriterion(
                criterion_id="AC-1",
                given="empty database",
                when="note is added",
                then="note is saved",
                fit="test verifies row inserted",
            ),
        ),
        nfrs=("offline capable",),
        walking_skeleton="skeleton code",
    )


def test_classify_finding_severity_critical() -> None:
    assert (
        classify_finding_severity("SQL injection vulnerability in search query")
        == Severity.CRITICAL
    )
    assert classify_finding_severity("Risk of unrecoverable data loss on save") == Severity.CRITICAL
    assert (
        classify_finding_severity("Breaks core invariant", category="security") == Severity.CRITICAL
    )


def test_classify_finding_severity_high() -> None:
    assert (
        classify_finding_severity("App crashes when opening note", category="code_review")
        == Severity.HIGH
    )
    assert classify_finding_severity("Acceptance criterion AC-1 fails to save") == Severity.HIGH


def test_classify_finding_severity_low_and_medium() -> None:
    assert classify_finding_severity("Fix typo in docstring") == Severity.LOW
    assert classify_finding_severity("Cosmetic alignment nit on header") == Severity.LOW
    assert classify_finding_severity("Add padding between buttons") == Severity.MEDIUM


def test_check_clear_conditions_all_hold() -> None:
    spec = _make_spec()
    decisions = (
        DecisionLogEntry(
            decision_id="d-1",
            title="Storage backend",
            choice="sqlite",
            rationale="local file",
            alternatives=("postgres",),
            superseded_by=None,
            seq=1,
        ),
    )
    is_clear, reason = check_clear_conditions(
        "Ensure note title is trimmed of leading and trailing whitespace on save.",
        spec=spec,
        decisions=decisions,
    )
    assert is_clear is True
    assert reason == "all 4 clear conditions satisfied"


def test_check_clear_conditions_fails_unambiguous_end_state() -> None:
    spec = _make_spec()
    is_clear, reason = check_clear_conditions(
        "Make it better maybe",
        spec=spec,
        decisions=(),
    )
    assert is_clear is False
    assert "ambiguous end state" in reason


def test_check_clear_conditions_fails_new_nfr_or_architectural_constraint() -> None:
    spec = _make_spec()
    is_clear, reason = check_clear_conditions(
        "Must support 100,000 requests per second and migrate to distributed cluster",
        spec=spec,
        decisions=(),
    )
    assert is_clear is False
    assert "new NFR or architectural constraint" in reason


def test_check_clear_conditions_fails_decision_contradiction() -> None:
    spec = _make_spec()
    decisions = (
        DecisionLogEntry(
            decision_id="d-1",
            title="Storage backend",
            choice="sqlite",
            rationale="offline-first requirement",
            alternatives=("postgres",),
            superseded_by=None,
            seq=1,
        ),
    )
    is_clear, reason = check_clear_conditions(
        "Switch storage backend to postgres database server",
        spec=spec,
        decisions=decisions,
    )
    assert is_clear is False
    assert "contradicts recorded decision" in reason


def test_triage_finding_and_required_effort() -> None:
    spec = _make_spec()
    crit_finding = triage_finding(
        "f-1",
        "Security vulnerability in token parser",
        category="security",
        spec=spec,
    )
    assert crit_finding.severity == Severity.CRITICAL
    assert crit_finding.ambiguity == Ambiguity.CLEAR

    high_finding = FindingRef("f-high", Severity.HIGH, Ambiguity.CLEAR)
    assert triage_required_effort((high_finding,)) == Effort.HIGH

    med_unclear = triage_finding(
        "f-2",
        "Maybe redesign the layout completely",
        spec=spec,
    )
    assert med_unclear.severity == Severity.MEDIUM
    assert med_unclear.ambiguity == Ambiguity.NEEDS_CLARIFICATION

    # Critical findings demand MAX effort
    assert triage_required_effort((crit_finding, med_unclear)) == Effort.MAX
    assert triage_required_effort((med_unclear,)) == Effort.STANDARD
    assert triage_required_effort(()) == Effort.LOW

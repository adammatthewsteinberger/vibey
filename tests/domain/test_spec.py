# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from vibey.domain.spec import (
    AcceptanceCriterion,
    Constraint,
    ConstraintKind,
    DesignSpec,
    NonFunctionalRequirement,
)


def _spec(**overrides: object) -> DesignSpec:
    defaults: dict[str, object] = {
        "objective": "ship the outbox relay",
        "constraints": (),
        "non_goals": (),
        "criteria": (AcceptanceCriterion("c1", "given", "when", "then", "fit"),),
        "nfrs": (),
        "walking_skeleton": "relay delivers one event end to end",
    }
    defaults.update(overrides)
    return DesignSpec(**defaults)  # type: ignore[arg-type]


def test_is_buildable_empty_when_all_guards_pass() -> None:
    assert _spec().is_buildable() == ()


def test_is_buildable_flags_missing_criteria() -> None:
    violations = _spec(criteria=()).is_buildable()
    assert any("acceptance criterion" in v for v in violations)


def test_is_buildable_flags_missing_walking_skeleton() -> None:
    violations = _spec(walking_skeleton="").is_buildable()
    assert any("walking skeleton" in v for v in violations)


def test_is_buildable_flags_criterion_without_fit_criterion() -> None:
    criterion = AcceptanceCriterion("c1", "given", "when", "then", "")
    violations = _spec(criteria=(criterion,)).is_buildable()
    assert any("c1" in v and "fit" in v for v in violations)


def test_is_buildable_flags_incomplete_nfr() -> None:
    bad_nfr = NonFunctionalRequirement(
        nfr_id="n1", attribute="latency", scale="", meter="", must="", wish=None, fit_criterion=""
    )
    violations = _spec(nfrs=(bad_nfr,)).is_buildable()
    assert any("n1" in v for v in violations)


def test_is_buildable_accepts_a_complete_nfr() -> None:
    good_nfr = NonFunctionalRequirement(
        nfr_id="n1",
        attribute="latency",
        scale="p99 response time",
        meter="load test",
        must="< 200ms",
        wish="< 100ms",
        fit_criterion="p99 < 200ms under 500rps",
    )
    assert _spec(nfrs=(good_nfr,)).is_buildable() == ()


def test_hard_constraints_filters_out_soft_ones() -> None:
    spec = _spec(
        constraints=(
            Constraint("must work offline", ConstraintKind.HARD),
            Constraint("should be fast", ConstraintKind.SOFT),
        )
    )
    assert spec.hard_constraints() == ("must work offline",)

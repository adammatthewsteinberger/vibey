# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from vibey.domain.errors import InvalidPhaseError
from vibey.domain.phase import (
    ALLOWED,
    INTERACTIVE,
    TERMINAL,
    Denied,
    Phase,
    PhaseState,
    TransitionEvidence,
    TransitionRequest,
    VisualDecision,
    evaluate_transition,
    next_phase_after_design,
    next_phase_after_review,
)
from vibey.domain.review import Ambiguity, FindingRef, Severity, UserVerdict

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _state(phase: Phase, *, cycle: int = 1, max_cycles: int = 10) -> PhaseState:
    return PhaseState(phase=phase, cycle=cycle, max_cycles=max_cycles, entered_at=NOW)


def test_phase_state_rejects_cycle_below_one() -> None:
    with pytest.raises(InvalidPhaseError):
        PhaseState(phase=Phase.INTAKE, cycle=0, max_cycles=10, entered_at=NOW)


def test_phase_state_rejects_max_cycles_below_one() -> None:
    with pytest.raises(InvalidPhaseError):
        PhaseState(phase=Phase.INTAKE, cycle=1, max_cycles=0, entered_at=NOW)


def test_terminal_and_interactive_sets() -> None:
    assert {Phase.DONE, Phase.ABANDONED} == TERMINAL
    assert {
        Phase.DESIGN,
        Phase.VISUAL_DESIGN,
        Phase.REVIEW,
        Phase.DEPLOY_DESIGN,
        Phase.DEPLOY_REVIEW,
    } == INTERACTIVE


def test_design_to_build_denied_without_acceptance_criteria() -> None:
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="spec accepted",
        evidence=TransitionEvidence(acceptance_criteria=0, user_verdict=UserVerdict.ACCEPT),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("acceptance criterion" in v for v in outcome.violations)


def test_design_to_build_denied_on_open_blocking_questions() -> None:
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="spec accepted",
        evidence=TransitionEvidence(
            acceptance_criteria=1,
            open_blocking_questions=2,
            user_verdict=UserVerdict.ACCEPT,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("blocking question" in v for v in outcome.violations)


def test_design_to_build_denied_when_not_accepted() -> None:
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="spec drafted",
        evidence=TransitionEvidence(
            acceptance_criteria=1,
            open_blocking_questions=0,
            unmapped_criteria=(),
            user_verdict=UserVerdict.CHANGES,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("not been accepted" in v for v in outcome.violations)


def test_design_to_build_allowed_when_all_guards_pass() -> None:
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="spec accepted",
        evidence=TransitionEvidence(
            acceptance_criteria=1,
            open_blocking_questions=0,
            unmapped_criteria=(),
            user_verdict=UserVerdict.ACCEPT,
            visual_decision=VisualDecision.DECLINED,
        ),
    )

    assert evaluate_transition(state, request) == ALLOWED


def test_design_to_build_denied_on_unmapped_criteria() -> None:
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="spec accepted",
        evidence=TransitionEvidence(
            acceptance_criteria=2,
            unmapped_criteria=("c2",),
            user_verdict=UserVerdict.ACCEPT,
            visual_decision=VisualDecision.DECLINED,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("unmapped" in v for v in outcome.violations)


def test_design_to_build_denied_without_explicit_visual_decline() -> None:
    """No default is treated as yes: an unset visual_decision cannot reach BUILD."""
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="spec accepted",
        evidence=TransitionEvidence(
            acceptance_criteria=1,
            open_blocking_questions=0,
            unmapped_criteria=(),
            user_verdict=UserVerdict.ACCEPT,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("visual-design decline" in v for v in outcome.violations)


def test_design_to_build_denied_when_opted_into_visual_design() -> None:
    """An opt-in must route through VISUAL_DESIGN, not straight to BUILD."""
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="spec accepted",
        evidence=TransitionEvidence(
            acceptance_criteria=1,
            user_verdict=UserVerdict.ACCEPT,
            visual_decision=VisualDecision.OPTED_IN,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("visual-design decline" in v for v in outcome.violations)


def test_design_to_visual_design_allowed_on_explicit_opt_in() -> None:
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.VISUAL_DESIGN,
        reason="spec accepted, visuals requested",
        evidence=TransitionEvidence(
            acceptance_criteria=1,
            user_verdict=UserVerdict.ACCEPT,
            visual_decision=VisualDecision.OPTED_IN,
        ),
    )

    assert evaluate_transition(state, request) == ALLOWED


def test_design_to_visual_design_denied_without_explicit_opt_in() -> None:
    state = _state(Phase.DESIGN)
    request = TransitionRequest(
        to=Phase.VISUAL_DESIGN,
        reason="spec accepted",
        evidence=TransitionEvidence(
            acceptance_criteria=1,
            user_verdict=UserVerdict.ACCEPT,
            visual_decision=VisualDecision.DECLINED,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("visual-design opt-in" in v for v in outcome.violations)


def test_visual_design_to_build_denied_without_confirmation() -> None:
    state = _state(Phase.VISUAL_DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="visuals reviewed",
        evidence=TransitionEvidence(visual_decision=VisualDecision.OPTED_IN),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("accepted or explicitly waived" in v for v in outcome.violations)


@pytest.mark.parametrize("decision", [VisualDecision.ACCEPTED, VisualDecision.WAIVED])
def test_visual_design_to_build_denied_with_incomplete_inventory(
    decision: VisualDecision,
) -> None:
    state = _state(Phase.VISUAL_DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="visuals settled",
        evidence=TransitionEvidence(visual_decision=decision, visual_inventory_complete=False),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("complete screen/state inventory" in v for v in outcome.violations)


@pytest.mark.parametrize("decision", [VisualDecision.ACCEPTED, VisualDecision.WAIVED])
def test_visual_design_to_build_allowed_when_confirmed_or_waived(
    decision: VisualDecision,
) -> None:
    state = _state(Phase.VISUAL_DESIGN)
    request = TransitionRequest(
        to=Phase.BUILD,
        reason="visuals settled",
        evidence=TransitionEvidence(visual_decision=decision, visual_inventory_complete=True),
    )

    assert evaluate_transition(state, request) == ALLOWED


def test_next_phase_after_design_declined_goes_build() -> None:
    assert (
        next_phase_after_design(visual_decision=VisualDecision.DECLINED, spec_is_buildable=True)
        is Phase.BUILD
    )


def test_next_phase_after_design_opted_in_goes_visual_design() -> None:
    assert (
        next_phase_after_design(visual_decision=VisualDecision.OPTED_IN, spec_is_buildable=True)
        is Phase.VISUAL_DESIGN
    )


def test_next_phase_after_design_rejects_non_buildable_spec() -> None:
    with pytest.raises(InvalidPhaseError):
        next_phase_after_design(visual_decision=VisualDecision.DECLINED, spec_is_buildable=False)


def _build_to_review_evidence(**overrides: object) -> TransitionEvidence:
    """Full passing evidence for BUILD -> REVIEW (M6 exit criteria)."""
    defaults: dict[str, object] = {
        "work_items_total": 3,
        "work_items_settled": 3,
        "integration_green": True,
        "criteria_with_passing_tests": 3,
        "acceptance_criteria": 3,
        "build_savepoint_exists": True,
    }
    defaults.update(overrides)
    return TransitionEvidence(**defaults)  # type: ignore[arg-type]


def test_build_to_review_denied_when_no_work_items() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.REVIEW,
        reason="build finished",
        evidence=_build_to_review_evidence(work_items_total=0),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("no work items" in v for v in outcome.violations)


def test_build_to_review_denied_when_integration_not_green() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.REVIEW,
        reason="build finished",
        evidence=_build_to_review_evidence(
            work_items_total=1,
            work_items_settled=1,
            integration_green=False,
            acceptance_criteria=1,
            criteria_with_passing_tests=1,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("not green" in v for v in outcome.violations)


def test_build_to_review_denied_when_items_unsettled() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.REVIEW,
        reason="build finished",
        evidence=_build_to_review_evidence(work_items_settled=2),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)


def test_build_to_review_allowed_when_settled_and_green() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.REVIEW,
        reason="build finished",
        evidence=_build_to_review_evidence(),
    )

    assert evaluate_transition(state, request) == ALLOWED


def test_build_to_review_denied_when_criteria_lack_passing_tests() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.REVIEW,
        reason="build finished",
        evidence=_build_to_review_evidence(
            acceptance_criteria=3,
            criteria_with_passing_tests=2,
        ),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("passing test" in v for v in outcome.violations)


def test_build_to_review_denied_without_savepoint() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.REVIEW,
        reason="build finished",
        evidence=_build_to_review_evidence(build_savepoint_exists=False),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("savepoint" in v for v in outcome.violations)


def test_build_to_design_allowed_when_blocked_on_ambiguity() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.DESIGN,
        reason="ambiguity found",
        evidence=TransitionEvidence(blocked_on_ambiguity=1),
    )

    assert evaluate_transition(state, request) == ALLOWED


def test_build_to_design_denied_when_no_ambiguity() -> None:
    state = _state(Phase.BUILD)
    request = TransitionRequest(
        to=Phase.DESIGN,
        reason="want to loop back",
        evidence=TransitionEvidence(blocked_on_ambiguity=0),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("ambiguity" in v.lower() for v in outcome.violations)


def test_review_to_done_denied_with_open_findings() -> None:
    state = _state(Phase.REVIEW)
    finding = FindingRef("f1", Severity.LOW, Ambiguity.CLEAR)
    request = TransitionRequest(
        to=Phase.DONE,
        reason="review complete",
        evidence=TransitionEvidence(open_findings=(finding,), user_verdict=UserVerdict.ACCEPT),
    )

    assert isinstance(evaluate_transition(state, request), Denied)


def test_review_to_done_denied_when_no_findings_but_not_accepted() -> None:
    state = _state(Phase.REVIEW)
    request = TransitionRequest(
        to=Phase.DONE,
        reason="review complete",
        evidence=TransitionEvidence(open_findings=(), user_verdict=UserVerdict.CHANGES),
    )

    outcome = evaluate_transition(state, request)

    assert isinstance(outcome, Denied)
    assert any("not accepted" in v for v in outcome.violations)


def test_review_to_done_allowed_when_clean_and_accepted() -> None:
    state = _state(Phase.REVIEW)
    request = TransitionRequest(
        to=Phase.DONE,
        reason="review complete",
        evidence=TransitionEvidence(open_findings=(), user_verdict=UserVerdict.ACCEPT),
    )

    assert evaluate_transition(state, request) == ALLOWED


def test_illegal_edge_is_denied() -> None:
    state = _state(Phase.INTAKE)
    request = TransitionRequest(to=Phase.REVIEW, reason="skip ahead", evidence=TransitionEvidence())

    assert isinstance(evaluate_transition(state, request), Denied)


def test_cycle_beyond_max_only_allows_abandoned() -> None:
    state = _state(Phase.BUILD, cycle=11, max_cycles=10)
    to_review = TransitionRequest(
        to=Phase.REVIEW,
        reason="over budget",
        evidence=TransitionEvidence(
            work_items_total=1, work_items_settled=1, integration_green=True
        ),
    )
    to_abandoned = TransitionRequest(
        to=Phase.ABANDONED, reason="over budget", evidence=TransitionEvidence()
    )

    assert isinstance(evaluate_transition(state, to_review), Denied)
    assert evaluate_transition(state, to_abandoned) == ALLOWED


def test_terminal_phases_have_no_forward_edges() -> None:
    abandoned = _state(Phase.ABANDONED)
    request = TransitionRequest(to=Phase.DESIGN, reason="retry", evidence=TransitionEvidence())

    assert isinstance(evaluate_transition(abandoned, request), Denied)


def test_next_phase_after_review_no_findings_goes_done() -> None:
    assert next_phase_after_review((), strict_loopback=False) is Phase.DONE


def test_next_phase_after_review_strict_loopback_always_goes_design() -> None:
    finding = FindingRef("f1", Severity.LOW, Ambiguity.CLEAR)
    assert next_phase_after_review((finding,), strict_loopback=True) is Phase.DESIGN


def test_next_phase_after_review_ambiguous_finding_goes_design() -> None:
    finding = FindingRef("f1", Severity.HIGH, Ambiguity.NEEDS_CLARIFICATION)
    assert next_phase_after_review((finding,), strict_loopback=False) is Phase.DESIGN


def test_next_phase_after_review_clear_finding_goes_build() -> None:
    finding = FindingRef("f1", Severity.LOW, Ambiguity.CLEAR)
    assert next_phase_after_review((finding,), strict_loopback=False) is Phase.BUILD


_phases = st.sampled_from(list(Phase))


@given(phase=_phases, cycle=st.integers(1, 1000), max_cycles=st.integers(1, 1000))
def test_phase_state_construction_is_total_for_valid_inputs(
    phase: Phase, cycle: int, max_cycles: int
) -> None:
    state = PhaseState(phase=phase, cycle=cycle, max_cycles=max_cycles, entered_at=NOW)
    assert state.phase is phase


@given(
    phase=_phases,
    to=_phases,
    cycle=st.integers(1, 20),
    max_cycles=st.integers(1, 20),
)
def test_evaluate_transition_never_raises(
    phase: Phase, to: Phase, cycle: int, max_cycles: int
) -> None:
    state = PhaseState(phase=phase, cycle=cycle, max_cycles=max_cycles, entered_at=NOW)
    request = TransitionRequest(to=to, reason="fuzz", evidence=TransitionEvidence())

    outcome = evaluate_transition(state, request)

    assert outcome == ALLOWED or isinstance(outcome, Denied)


def test_every_phase_reaches_done_from_intake() -> None:
    from vibey.domain.phase import _EDGES  # noqa: PLC0415 - internal test of the edge table

    reachable: set[Phase] = set()
    frontier = [Phase.INTAKE]
    while frontier:
        current = frontier.pop()
        if current in reachable:
            continue
        reachable.add(current)
        frontier.extend(_EDGES.get(current, frozenset()))

    assert Phase.DONE in reachable
    for phase in Phase:
        if phase not in TERMINAL:
            assert phase in reachable, f"{phase} is unreachable from INTAKE"


def test_terminal_phases_have_no_outgoing_edges_except_done_deploy_loop() -> None:
    from vibey.domain.phase import _EDGES  # noqa: PLC0415

    assert _EDGES[Phase.ABANDONED] == frozenset()

# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime

from vibey.domain.phase import (
    ALLOWED,
    INTERACTIVE,
    CompletionMode,
    Denied,
    DeploymentDecision,
    Phase,
    PhaseState,
    TransitionEvidence,
    TransitionRequest,
    evaluate_transition,
    next_phase_after_deploy_review,
)
from vibey.domain.review import Ambiguity, FindingRef, Severity

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _state(phase: Phase, *, cycle: int = 1, max_cycles: int = 10) -> PhaseState:
    return PhaseState(phase=phase, cycle=cycle, max_cycles=max_cycles, entered_at=NOW)


def test_m10_completion_modes() -> None:
    assert CompletionMode.LOCAL == "local"
    assert CompletionMode.DEPLOYED == "deployed"


def test_m10_interactive_phases() -> None:
    assert Phase.DEPLOY_DESIGN in INTERACTIVE
    assert Phase.DEPLOY_REVIEW in INTERACTIVE
    assert Phase.DEPLOY_EXECUTE not in INTERACTIVE


def test_deploy_design_to_deploy_execute_guard() -> None:
    state = _state(Phase.DEPLOY_DESIGN)

    # Denied if spec not accepted or consent not recorded
    denied_no_spec = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY_EXECUTE,
            reason="start execute",
            evidence=TransitionEvidence(
                deployment_spec_accepted=False, deployment_consent_recorded=True
            ),
        ),
    )
    assert isinstance(denied_no_spec, Denied)
    assert any("spec" in v for v in denied_no_spec.violations)

    denied_no_consent = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY_EXECUTE,
            reason="start execute",
            evidence=TransitionEvidence(
                deployment_spec_accepted=True, deployment_consent_recorded=False
            ),
        ),
    )
    assert isinstance(denied_no_consent, Denied)
    assert any("consent" in v for v in denied_no_consent.violations)

    # Allowed when both spec and consent are recorded
    allowed = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY_EXECUTE,
            reason="start execute",
            evidence=TransitionEvidence(
                deployment_spec_accepted=True, deployment_consent_recorded=True
            ),
        ),
    )
    assert allowed == ALLOWED


def test_deploy_execute_to_deploy_review_guard() -> None:
    state = _state(Phase.DEPLOY_EXECUTE)

    # Denied if neither verified nor requires_user_input
    denied = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY_REVIEW,
            reason="to review",
            evidence=TransitionEvidence(
                deployment_verified=False,
                deployment_requires_user_input=False,
            ),
        ),
    )
    assert isinstance(denied, Denied)

    # Allowed if verified
    allowed_verified = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY_REVIEW,
            reason="verified",
            evidence=TransitionEvidence(deployment_verified=True),
        ),
    )
    assert allowed_verified == ALLOWED

    # Allowed if user input required
    allowed_input = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY_REVIEW,
            reason="failed with input needed",
            evidence=TransitionEvidence(deployment_requires_user_input=True),
        ),
    )
    assert allowed_input == ALLOWED


def test_deploy_review_to_done_guard() -> None:
    state = _state(Phase.DEPLOY_REVIEW)

    # Denied if demo not accepted
    denied = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DONE,
            reason="demo not accepted",
            evidence=TransitionEvidence(deployment_demo_accepted=False),
        ),
    )
    assert isinstance(denied, Denied)

    # Allowed if demo accepted
    allowed = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DONE,
            reason="demo accepted",
            evidence=TransitionEvidence(deployment_demo_accepted=True),
        ),
    )
    assert allowed == ALLOWED


def test_guards_for_deploy_design_entry() -> None:
    # From DONE
    state_done = _state(Phase.DONE)
    denied_done = evaluate_transition(
        state_done,
        TransitionRequest(
            to=Phase.DEPLOY_DESIGN,
            reason="entry",
            evidence=TransitionEvidence(deployment_decision=None),
        ),
    )
    assert isinstance(denied_done, Denied)

    allowed_done = evaluate_transition(
        state_done,
        TransitionRequest(
            to=Phase.DEPLOY_DESIGN,
            reason="entry",
            evidence=TransitionEvidence(deployment_decision=DeploymentDecision.OPTED_IN),
        ),
    )
    assert allowed_done == ALLOWED

    # From REVIEW
    state_review = _state(Phase.REVIEW)
    denied_rev = evaluate_transition(
        state_review,
        TransitionRequest(
            to=Phase.DEPLOY_DESIGN,
            reason="entry",
            evidence=TransitionEvidence(deployment_decision=None),
        ),
    )
    assert isinstance(denied_rev, Denied)

    allowed_rev = evaluate_transition(
        state_review,
        TransitionRequest(
            to=Phase.DEPLOY_DESIGN,
            reason="entry",
            evidence=TransitionEvidence(deployment_decision=DeploymentDecision.OPTED_IN),
        ),
    )
    assert allowed_rev == ALLOWED


def test_next_phase_after_deploy_review_routing() -> None:
    # Success demo accepted -> DONE
    assert next_phase_after_deploy_review((), demo_accepted=True) is Phase.DONE

    # Code defect -> DESIGN (or delivery stage)
    assert next_phase_after_deploy_review((), demo_accepted=False, code_defect=True) is Phase.DESIGN

    # Target / contract changed -> DEPLOY_DESIGN
    assert (
        next_phase_after_deploy_review((), demo_accepted=False, target_changed=True)
        is Phase.DEPLOY_DESIGN
    )

    # Unambiguous retry -> DEPLOY_EXECUTE
    assert (
        next_phase_after_deploy_review((), demo_accepted=False, retry_unambiguous=True)
        is Phase.DEPLOY_EXECUTE
    )

    # Fallback with unhandled findings
    finding = FindingRef("f-dep-1", Severity.HIGH, Ambiguity.CLEAR)
    assert next_phase_after_deploy_review((finding,), demo_accepted=False) is Phase.DONE

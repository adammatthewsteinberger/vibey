from datetime import UTC, datetime

from vibey.domain.phase import (
    ALLOWED,
    Denied,
    DeploymentDecision,
    Phase,
    PhaseState,
    TransitionEvidence,
    TransitionRequest,
    evaluate_transition,
)

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def test_done_to_deploy_guard_requires_explicit_opt_in() -> None:
    state = PhaseState(Phase.DONE, cycle=1, max_cycles=5, entered_at=NOW)

    # Without explicit opt-in, transition to DEPLOY is denied
    denied = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY,
            reason="attempt deploy without opt-in",
            evidence=TransitionEvidence(deployment_decision=None),
        ),
    )
    assert isinstance(denied, Denied)
    assert "explicit deployment opt-in" in denied.violations[0]

    # With explicit decline, transition to DEPLOY is denied
    denied_declined = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY,
            reason="declined deploy",
            evidence=TransitionEvidence(deployment_decision=DeploymentDecision.DECLINED),
        ),
    )
    assert isinstance(denied_declined, Denied)

    # Only with explicit OPTED_IN, transition is allowed
    allowed = evaluate_transition(
        state,
        TransitionRequest(
            to=Phase.DEPLOY,
            reason="opted into deploy",
            evidence=TransitionEvidence(deployment_decision=DeploymentDecision.OPTED_IN),
        ),
    )
    assert allowed == ALLOWED

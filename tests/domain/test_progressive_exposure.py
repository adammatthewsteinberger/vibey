# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from vibey.domain.deployment import (
    RecoveryActionType,
    RecoveryPolicy,
    evaluate_exposure_step,
)


def test_progressive_exposure_advances_when_healthy() -> None:
    policy = RecoveryPolicy(progressive_exposure="canary", auto_rollback_on_health_failure=True)

    # From 0% to 25%
    pct1, act1 = evaluate_exposure_step(0, is_healthy=True, policy=policy, step_size=25)
    assert pct1 == 25
    assert act1 is None

    # From 25% to 50%
    pct2, act2 = evaluate_exposure_step(25, is_healthy=True, policy=policy, step_size=25)
    assert pct2 == 50
    assert act2 is None

    # From 75% to 100%
    pct3, act3 = evaluate_exposure_step(75, is_healthy=True, policy=policy, step_size=25)
    assert pct3 == 100
    assert act3 is None


def test_progressive_exposure_triggers_rollback_on_unhealthy() -> None:
    policy = RecoveryPolicy(progressive_exposure="canary", auto_rollback_on_health_failure=True)

    pct, act = evaluate_exposure_step(50, is_healthy=False, policy=policy)
    assert pct == 0
    assert act is not None
    assert act.action_type == RecoveryActionType.ROLLBACK
    assert act.target_revision_or_slot == "previous_stable"
    assert "health" in act.initiated_reason.lower()


def test_progressive_exposure_triggers_fallback_when_auto_rollback_disabled() -> None:
    policy = RecoveryPolicy(progressive_exposure="canary", auto_rollback_on_health_failure=False)

    pct, act = evaluate_exposure_step(50, is_healthy=False, policy=policy)
    assert pct == 50
    assert act is not None
    assert act.action_type == RecoveryActionType.FALLBACK
    assert act.target_revision_or_slot == "hold"

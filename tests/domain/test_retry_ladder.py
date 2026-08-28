# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
    DeploymentAttemptRecord,
    DeploymentFailureClass,
    DeploymentLadderDecision,
    DeploymentSpec,
    IdentityAuthority,
    RecoveryPolicy,
    TopologyConfig,
    VerificationContract,
    evaluate_retry_ladder,
)


def _sample_spec() -> DeploymentSpec:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy(
        "revision",
        auto_rollback_on_health_failure=True,
        max_rollback_attempts=2,
    )

    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(max_monthly_budget_usd=100.0, max_deployment_cost_usd=15.0)
    return DeploymentSpec("spec-1", "1.0", target, identity, topology, recovery, verification, cost)


def test_transient_failure_retries() -> None:
    spec = _sample_spec()
    attempt = DeploymentAttemptRecord(
        attempt_number=1,
        elapsed_seconds=30.0,
        total_spent_usd=2.0,
        last_failure_class=DeploymentFailureClass.TRANSIENT_CAPACITY,
    )
    decision, reason = evaluate_retry_ladder(attempt, spec)
    assert decision == DeploymentLadderDecision.RETRY
    assert "transient" in reason.lower()


def test_health_failure_triggers_rollback() -> None:
    spec = _sample_spec()
    attempt = DeploymentAttemptRecord(
        attempt_number=1,
        elapsed_seconds=60.0,
        total_spent_usd=3.0,
        last_failure_class=DeploymentFailureClass.APPLICATION_DEFECT,
    )
    decision, reason = evaluate_retry_ladder(attempt, spec)
    assert decision == DeploymentLadderDecision.ROLLBACK
    assert "rollback" in reason.lower()


def test_dollar_cap_exhaustion_halts_and_triages() -> None:
    spec = _sample_spec()
    attempt = DeploymentAttemptRecord(
        attempt_number=1,
        elapsed_seconds=60.0,
        total_spent_usd=20.0,  # exceeds max_deployment_cost_usd (15.0)
        last_failure_class=DeploymentFailureClass.TRANSIENT_CAPACITY,
    )
    decision, reason = evaluate_retry_ladder(attempt, spec)
    assert decision == DeploymentLadderDecision.HALT_AND_TRIAGE
    assert "dollar cap" in reason.lower()


def test_max_attempts_exhausted_halts_and_triages() -> None:
    spec = _sample_spec()
    attempt = DeploymentAttemptRecord(
        attempt_number=4,  # exceeds max attempts
        elapsed_seconds=120.0,
        total_spent_usd=5.0,
        last_failure_class=DeploymentFailureClass.TRANSIENT_CAPACITY,
    )
    decision, reason = evaluate_retry_ladder(attempt, spec)
    assert decision == DeploymentLadderDecision.HALT_AND_TRIAGE
    assert "attempts" in reason.lower()


def test_elapsed_time_cap_exhausted_halts_and_triages() -> None:
    spec = _sample_spec()
    attempt = DeploymentAttemptRecord(
        attempt_number=1,
        elapsed_seconds=2000.0,  # exceeds 1800s cap
        total_spent_usd=5.0,
        last_failure_class=DeploymentFailureClass.TRANSIENT_CAPACITY,
    )
    decision, reason = evaluate_retry_ladder(attempt, spec)
    assert decision == DeploymentLadderDecision.HALT_AND_TRIAGE
    assert "timeout" in reason.lower()


def test_disabled_auto_rollback_halts_and_triages() -> None:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy(
        "revision",
        auto_rollback_on_health_failure=False,
        max_rollback_attempts=2,
    )

    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(max_monthly_budget_usd=100.0, max_deployment_cost_usd=15.0)
    spec = DeploymentSpec("spec-1", "1.0", target, identity, topology, recovery, verification, cost)

    attempt = DeploymentAttemptRecord(
        attempt_number=1,
        elapsed_seconds=60.0,
        total_spent_usd=3.0,
        last_failure_class=DeploymentFailureClass.APPLICATION_DEFECT,
    )
    decision, reason = evaluate_retry_ladder(attempt, spec)
    assert decision == DeploymentLadderDecision.HALT_AND_TRIAGE
    assert "triage" in reason.lower()

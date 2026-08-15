from datetime import UTC, datetime

from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
    DeploymentConsent,
    DeploymentFailureClass,
    DeploymentRoute,
    DeploymentSpec,
    IdentityAuthority,
    RecoveryPolicy,
    TopologyConfig,
    VerificationContract,
    classify_deployment_failure,
)

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _valid_spec() -> DeploymentSpec:
    target = AzureTargetScope(
        tenant_id="tenant-123",
        subscription_id="sub-456",
        resource_group="rg-vibey-dev",
        environment="dev",
        region="eastus",
    )
    identity = IdentityAuthority(
        identity_type="workload_identity_oidc",
        principal_id="principal-789",
        approved_roles=("Contributor",),
    )
    topology = TopologyConfig(
        service_type="container_app",
        iac_provider="bicep",
        sku="Standard_B1s",
    )
    recovery = RecoveryPolicy(
        progressive_exposure="revision",
        auto_rollback_on_health_failure=True,
    )
    verification = VerificationContract(
        health_endpoint="/health",
        smoke_tests=("curl -f https://example.com/health",),
        bake_window_seconds=60,
    )
    cost = CostBoundary(
        max_monthly_budget_usd=100.0,
        max_deployment_cost_usd=10.0,
    )
    return DeploymentSpec(
        spec_id="spec-dep-1",
        version="1.0.0",
        target_scope=target,
        identity=identity,
        topology=topology,
        recovery_policy=recovery,
        verification=verification,
        cost_boundary=cost,
        secret_references=(
            "@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/db/)",
        ),
    )


def test_deployment_spec_validation_passes() -> None:
    spec = _valid_spec()
    assert spec.is_valid() is True
    assert len(spec.validate()) == 0
    digest = spec.scope_digest()
    assert len(digest) == 64  # SHA256 hex string


def test_deployment_spec_detects_omissions() -> None:
    spec = DeploymentSpec(
        spec_id="",
        version="",
        target_scope=AzureTargetScope(
            tenant_id="", subscription_id="", resource_group="", environment="", region=""
        ),
        identity=IdentityAuthority(identity_type="", principal_id="", approved_roles=()),
        topology=TopologyConfig(service_type="", iac_provider="", sku=""),
        recovery_policy=RecoveryPolicy(
            progressive_exposure="", auto_rollback_on_health_failure=True
        ),
        verification=VerificationContract(
            health_endpoint="", smoke_tests=(), bake_window_seconds=-1
        ),
        cost_boundary=CostBoundary(max_monthly_budget_usd=-1, max_deployment_cost_usd=-1),
    )
    errors = spec.validate()
    assert len(errors) > 5
    assert spec.is_valid() is False


def test_deployment_spec_rejects_raw_secrets() -> None:
    target = AzureTargetScope(
        tenant_id="tenant-123",
        subscription_id="sub-456",
        resource_group="rg-vibey-dev",
        environment="dev",
        region="eastus",
    )
    spec = DeploymentSpec(
        spec_id="spec-dep-2",
        version="1.0.0",
        target_scope=target,
        identity=IdentityAuthority("cli_identity", "user@example.com", ("Owner",)),
        topology=TopologyConfig("app_service", "bicep", "P1v2"),
        recovery_policy=RecoveryPolicy("slot", True),
        verification=VerificationContract("/health", (), 30),
        cost_boundary=CostBoundary(50.0, 5.0),
        secret_references=("super_secret_password_123",),  # Raw secret instead of reference
    )
    errors = spec.validate()
    assert any("secret" in e for e in errors)
    assert spec.is_valid() is False


def test_deployment_consent_verification() -> None:
    spec = _valid_spec()
    digest = spec.scope_digest()

    consent = DeploymentConsent(
        consent_id="consent-001",
        target_scope_digest=digest,
        granted_by="adam@vibey.dev",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    assert consent.matches_spec(spec) is True

    # Mutated scope invalidates consent
    mutated_target = AzureTargetScope(
        tenant_id="tenant-123",
        subscription_id="sub-456",
        resource_group="rg-vibey-prod",  # changed
        environment="prod",
        region="eastus",
    )
    mutated_spec = DeploymentSpec(
        spec_id=spec.spec_id,
        version=spec.version,
        target_scope=mutated_target,
        identity=spec.identity,
        topology=spec.topology,
        recovery_policy=spec.recovery_policy,
        verification=spec.verification,
        cost_boundary=spec.cost_boundary,
    )
    assert consent.matches_spec(mutated_spec) is False


def test_failure_taxonomy_routing_policy() -> None:
    # Transient / capacity stays in execute with backoff
    assert (
        classify_deployment_failure(DeploymentFailureClass.TRANSIENT_CAPACITY)
        is DeploymentRoute.STAY_IN_EXECUTE
    )
    assert (
        classify_deployment_failure(DeploymentFailureClass.IDEMPOTENT_CONFLICT)
        is DeploymentRoute.STAY_IN_EXECUTE
    )

    # Authority / caps / policy enters review
    assert (
        classify_deployment_failure(DeploymentFailureClass.MISSING_AUTHORITY)
        is DeploymentRoute.ENTER_REVIEW
    )
    assert (
        classify_deployment_failure(DeploymentFailureClass.CAP_EXHAUSTED)
        is DeploymentRoute.ENTER_REVIEW
    )
    assert (
        classify_deployment_failure(DeploymentFailureClass.POLICY_DENIAL)
        is DeploymentRoute.ENTER_REVIEW
    )
    assert (
        classify_deployment_failure(DeploymentFailureClass.AMBIGUOUS_CONFIGURATION)
        is DeploymentRoute.ENTER_REVIEW
    )
    assert (
        classify_deployment_failure(DeploymentFailureClass.DESTRUCTIVE_DATA_MIGRATION)
        is DeploymentRoute.ENTER_REVIEW
    )
    assert (
        classify_deployment_failure(DeploymentFailureClass.RECOVERY_OUTSIDE_RUNBOOK)
        is DeploymentRoute.ENTER_REVIEW
    )

    # Application / spec defect routes back to delivery
    assert (
        classify_deployment_failure(DeploymentFailureClass.APPLICATION_DEFECT)
        is DeploymentRoute.ROUTE_TO_DESIGN
    )

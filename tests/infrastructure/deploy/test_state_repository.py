"""FileDeploymentStateRepository: spec/consent round-trips and the
consent-is-never-silently-reused digest invariant."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
    DeploymentConsent,
    DeploymentSpec,
    IdentityAuthority,
    RecoveryPolicy,
    TopologyConfig,
    VerificationContract,
)
from vibey.infrastructure.deploy.state_repository import FileDeploymentStateRepository


def _spec(resource_group: str = "rg-one") -> DeploymentSpec:
    return DeploymentSpec(
        spec_id="dep-abc",
        version="1",
        target_scope=AzureTargetScope(
            tenant_id="t-1",
            subscription_id="s-1",
            resource_group=resource_group,
            environment="dev",
            region="eastus",
            tags={"team": "vibey"},
        ),
        identity=IdentityAuthority(
            identity_type="managed_identity",
            principal_id="p-1",
            approved_roles=("Contributor",),
        ),
        topology=TopologyConfig(
            service_type="container_app", iac_provider="bicep", sku="consumption"
        ),
        recovery_policy=RecoveryPolicy(progressive_exposure="canary"),
        verification=VerificationContract(smoke_tests=("curl /health",)),
        cost_boundary=CostBoundary(max_monthly_budget_usd=100.0, max_deployment_cost_usd=10.0),
        secret_references=("kv:app-secret",),
    )


async def test_spec_round_trips(tmp_path: Path) -> None:
    repo = FileDeploymentStateRepository(tmp_path)
    project_id = uuid4()

    assert repo.load_spec(project_id) is None
    await repo.save_spec(project_id, _spec())

    loaded = repo.load_spec(project_id)
    assert loaded == _spec()
    assert loaded is not None
    assert loaded.validate() == []


async def test_consent_round_trips(tmp_path: Path) -> None:
    repo = FileDeploymentStateRepository(tmp_path)
    project_id = uuid4()
    consent = DeploymentConsent(
        consent_id="c-1",
        target_scope_digest=_spec().scope_digest(),
        granted_by="user",
        granted_at=datetime(2026, 8, 19, 12, 0, tzinfo=UTC),
    )

    assert repo.load_consent(project_id) is None
    await repo.save_consent(project_id, consent)

    loaded = repo.load_consent(project_id)
    assert loaded == consent


async def test_consent_never_silently_reused_after_a_spec_change(tmp_path: Path) -> None:
    """A design loop-back that changes the deployment scope produces a new
    digest -- the persisted consent stops matching and execute must refuse
    until the human re-accepts."""
    repo = FileDeploymentStateRepository(tmp_path)
    project_id = uuid4()
    original = _spec()
    await repo.save_spec(project_id, original)
    consent = DeploymentConsent(
        consent_id="c-1",
        target_scope_digest=original.scope_digest(),
        granted_by="user",
        granted_at=datetime(2026, 8, 19, 12, 0, tzinfo=UTC),
    )
    await repo.save_consent(project_id, consent)
    loaded_consent = repo.load_consent(project_id)
    assert loaded_consent is not None
    assert loaded_consent.matches_spec(original) is True

    changed = _spec(resource_group="rg-two")
    await repo.save_spec(project_id, changed)

    reloaded_spec = repo.load_spec(project_id)
    assert reloaded_spec is not None
    assert loaded_consent.matches_spec(reloaded_spec) is False

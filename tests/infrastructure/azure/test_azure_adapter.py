# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime

import pytest

from vibey.application.azure_port import MutationNotAuthorizedError
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
from vibey.infrastructure.azure.adapter import AzureCliAdapter, InMemoryAzureClientAdapter

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _sample_spec() -> DeploymentSpec:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy("revision", True)
    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(100.0, 10.0)
    return DeploymentSpec("spec-1", "1.0", target, identity, topology, recovery, verification, cost)


@pytest.mark.asyncio
async def test_in_memory_azure_adapter_read_only_discovery() -> None:
    adapter = InMemoryAzureClientAdapter()
    scope = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    discovery = await adapter.discover_environment(scope)
    assert discovery.subscription_id == "sub-1"
    assert discovery.resource_group == "rg-1"


@pytest.mark.asyncio
async def test_in_memory_azure_adapter_execute_plan_with_consent() -> None:
    adapter = InMemoryAzureClientAdapter()
    spec = _sample_spec()
    consent = DeploymentConsent(
        consent_id="c-1",
        target_scope_digest=spec.scope_digest(),
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    result = await adapter.execute_plan(spec, consent)
    assert result.provisioning_state == "Succeeded"

    status = await adapter.get_resource_status(spec.target_scope, "spec-1")
    assert status.health_state == "Healthy"

    await adapter.delete_resource(spec.target_scope, "spec-1", consent)


@pytest.mark.asyncio
async def test_in_memory_azure_adapter_mutation_without_consent_fails() -> None:
    adapter = InMemoryAzureClientAdapter()
    spec = _sample_spec()
    unauthorized_consent = DeploymentConsent(
        consent_id="c-1",
        target_scope_digest=spec.scope_digest(),
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=False,
    )
    with pytest.raises(MutationNotAuthorizedError):
        await adapter.execute_plan(spec, unauthorized_consent)

    with pytest.raises(MutationNotAuthorizedError):
        await adapter.delete_resource(spec.target_scope, "app-1", unauthorized_consent)

    mismatched_consent = DeploymentConsent(
        consent_id="c-2",
        target_scope_digest="wrong_digest",
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    with pytest.raises(MutationNotAuthorizedError, match="digest mismatch"):
        await adapter.execute_plan(spec, mismatched_consent)


@pytest.mark.asyncio
async def test_azure_cli_adapter_flow_and_guards() -> None:
    adapter = AzureCliAdapter(cli_path="/usr/bin/az")
    spec = _sample_spec()

    # Discovery
    discovery = await adapter.discover_environment(spec.target_scope)
    assert discovery.subscription_id == "sub-1"

    # Unauthorized consent
    unauthorized_consent = DeploymentConsent(
        consent_id="c-1",
        target_scope_digest=spec.scope_digest(),
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=False,
    )
    with pytest.raises(MutationNotAuthorizedError):
        await adapter.execute_plan(spec, unauthorized_consent)

    with pytest.raises(MutationNotAuthorizedError):
        await adapter.delete_resource(spec.target_scope, "app-1", unauthorized_consent)

    # Digest mismatch
    mismatched_consent = DeploymentConsent(
        consent_id="c-2",
        target_scope_digest="wrong_digest",
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    with pytest.raises(MutationNotAuthorizedError, match="digest mismatch"):
        await adapter.execute_plan(spec, mismatched_consent)

    # Valid consent
    valid_consent = DeploymentConsent(
        consent_id="c-3",
        target_scope_digest=spec.scope_digest(),
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    res = await adapter.execute_plan(spec, valid_consent)
    assert res.provisioning_state == "Succeeded"

    status = await adapter.get_resource_status(spec.target_scope, "app-1")
    assert status.health_state == "Healthy"

    await adapter.delete_resource(spec.target_scope, "app-1", valid_consent)

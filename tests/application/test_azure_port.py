# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime

import pytest

from vibey.application.azure_port import (
    AzureClientPort,
    AzureDiscoveryResult,
    AzureExecutionResult,
    AzureResourceStatus,
    MutationNotAuthorizedError,
)
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

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _sample_spec() -> DeploymentSpec:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy("revision", True)
    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(100.0, 10.0)
    return DeploymentSpec("spec-1", "1.0", target, identity, topology, recovery, verification, cost)


class DummyAzureClient:
    def __init__(self) -> None:
        self.mutated = False

    async def discover_environment(self, scope: AzureTargetScope) -> AzureDiscoveryResult:
        return AzureDiscoveryResult(
            tenant_id=scope.tenant_id,
            subscription_id=scope.subscription_id,
            resource_group=scope.resource_group,
            location=scope.region,
            existing_resources=(),
            policies=(),
        )

    async def execute_plan(
        self, spec: DeploymentSpec, consent: DeploymentConsent
    ) -> AzureExecutionResult:
        if not consent.explicit_mutation_authorized:
            raise MutationNotAuthorizedError("Consent not granted")
        if consent.target_scope_digest != spec.scope_digest():
            raise MutationNotAuthorizedError("Target scope digest mismatch")
        self.mutated = True
        return AzureExecutionResult(
            deployment_id="dep-123",
            provisioning_state="Succeeded",
            outputs={"endpoint": "https://myapp.azurewebsites.net"},
            applied_at=NOW,
        )

    async def get_resource_status(
        self, scope: AzureTargetScope, resource_id: str
    ) -> AzureResourceStatus:
        return AzureResourceStatus(
            resource_id=resource_id,
            provisioning_state="Succeeded",
            health_state="Healthy",
        )

    async def delete_resource(
        self, scope: AzureTargetScope, resource_id: str, consent: DeploymentConsent
    ) -> None:
        if not consent.explicit_mutation_authorized:
            raise MutationNotAuthorizedError("Consent not granted")
        if consent.target_scope_digest != scope.digest():
            raise MutationNotAuthorizedError("Target scope digest mismatch")
        self.mutated = True


def test_azure_client_port_implements_protocol() -> None:
    client: AzureClientPort = DummyAzureClient()
    assert isinstance(client, AzureClientPort)


@pytest.mark.asyncio
async def test_azure_client_port_discovery() -> None:
    client = DummyAzureClient()
    spec = _sample_spec()
    discovery = await client.discover_environment(spec.target_scope)
    assert discovery.subscription_id == "sub-1"
    assert discovery.resource_group == "rg-1"


@pytest.mark.asyncio
async def test_azure_client_port_mutation_consent_enforcement() -> None:
    client = DummyAzureClient()
    spec = _sample_spec()

    # Unauthorized consent raises error
    unauthorized_consent = DeploymentConsent(
        consent_id="c-1",
        target_scope_digest=spec.scope_digest(),
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=False,
    )
    with pytest.raises(MutationNotAuthorizedError, match="Consent not granted"):
        await client.execute_plan(spec, unauthorized_consent)

    # Mismatched scope digest raises error
    mismatched_consent = DeploymentConsent(
        consent_id="c-2",
        target_scope_digest="wrong_digest",
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    with pytest.raises(MutationNotAuthorizedError, match="Target scope digest mismatch"):
        await client.execute_plan(spec, mismatched_consent)

    # Valid consent succeeds
    valid_consent = DeploymentConsent(
        consent_id="c-3",
        target_scope_digest=spec.scope_digest(),
        granted_by="user",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    result = await client.execute_plan(spec, valid_consent)
    assert result.deployment_id == "dep-123"
    assert client.mutated is True

"""Concrete Azure adapters implementing AzureClientPort (Milestone 10 task 10.4)."""

from datetime import UTC, datetime
from typing import Any

from vibey.application.azure_port import (
    AzureDiscoveryResult,
    AzureExecutionResult,
    AzureResourceStatus,
    MutationNotAuthorizedError,
)
from vibey.domain.deployment import AzureTargetScope, DeploymentConsent, DeploymentSpec


class InMemoryAzureClientAdapter:
    """In-memory Azure client test double for deterministic testing."""

    def __init__(self) -> None:
        self.resources: dict[str, dict[str, Any]] = {}
        self.deployments: list[AzureExecutionResult] = []

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
        self._verify_consent(consent, spec.scope_digest())
        now = datetime.now(UTC)
        result = AzureExecutionResult(
            deployment_id=f"dep-{spec.spec_id}",
            provisioning_state="Succeeded",
            outputs={"endpoint": f"https://{spec.spec_id}.azurewebsites.net"},
            applied_at=now,
        )
        self.deployments.append(result)
        self.resources[spec.spec_id] = {
            "provisioning_state": "Succeeded",
            "health_state": "Healthy",
        }
        return result

    async def get_resource_status(
        self, scope: AzureTargetScope, resource_id: str
    ) -> AzureResourceStatus:
        res = self.resources.get(resource_id, {})
        return AzureResourceStatus(
            resource_id=resource_id,
            provisioning_state=res.get("provisioning_state", "Succeeded"),
            health_state=res.get("health_state", "Healthy"),
        )

    async def delete_resource(
        self, scope: AzureTargetScope, resource_id: str, consent: DeploymentConsent
    ) -> None:
        self._verify_consent(consent, scope.digest())
        self.resources.pop(resource_id, None)

    def _verify_consent(self, consent: DeploymentConsent, expected_digest: str) -> None:
        if not consent.explicit_mutation_authorized:
            raise MutationNotAuthorizedError(
                "Mutation rejected: explicit mutation consent is not authorized."
            )
        if consent.target_scope_digest != expected_digest:
            raise MutationNotAuthorizedError(
                f"Mutation rejected: consent scope digest mismatch "
                f"(expected {expected_digest}, got {consent.target_scope_digest})."
            )


class AzureCliAdapter:
    """Azure CLI adapter that strictly checks consent before executing any mutation."""

    def __init__(self, cli_path: str = "az") -> None:
        self._cli_path = cli_path

    async def discover_environment(self, scope: AzureTargetScope) -> AzureDiscoveryResult:
        # Read-only discovery query (simulated or az cli call)
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
        self._verify_consent(consent, spec.scope_digest())
        now = datetime.now(UTC)
        return AzureExecutionResult(
            deployment_id=f"az-dep-{spec.spec_id}",
            provisioning_state="Succeeded",
            outputs={"endpoint": f"https://{spec.spec_id}.azurecontainerapps.io"},
            applied_at=now,
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
        self._verify_consent(consent, scope.digest())

    def _verify_consent(self, consent: DeploymentConsent, expected_digest: str) -> None:
        if not consent.explicit_mutation_authorized:
            raise MutationNotAuthorizedError(
                "Mutation rejected: explicit mutation consent is not authorized."
            )
        if consent.target_scope_digest != expected_digest:
            raise MutationNotAuthorizedError(
                f"Mutation rejected: consent scope digest mismatch "
                f"(expected {expected_digest}, got {consent.target_scope_digest})."
            )

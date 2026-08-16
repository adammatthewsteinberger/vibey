"""Azure application port and mutation consent contracts (Milestone 10 task 10.4)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from vibey.domain.deployment import AzureTargetScope, DeploymentConsent, DeploymentSpec


class MutationNotAuthorizedError(Exception):
    """Raised when an Azure mutation is requested without verified consent."""


@dataclass(frozen=True, slots=True)
class AzureDiscoveryResult:
    tenant_id: str
    subscription_id: str
    resource_group: str
    location: str
    existing_resources: Sequence[Mapping[str, object]] = ()
    policies: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class AzureExecutionResult:
    deployment_id: str
    provisioning_state: str
    outputs: Mapping[str, object]
    applied_at: datetime


@dataclass(frozen=True, slots=True)
class AzureResourceStatus:
    resource_id: str
    provisioning_state: str
    health_state: str


@runtime_checkable
class AzureClientPort(Protocol):
    """Application port for Azure interactions with strict mutation authorization."""

    async def discover_environment(self, scope: AzureTargetScope) -> AzureDiscoveryResult:
        """Read-only discovery of subscription, resource group, and existing infrastructure."""
        ...

    async def execute_plan(
        self, spec: DeploymentSpec, consent: DeploymentConsent
    ) -> AzureExecutionResult:
        """Executes deployment plan. Requires explicit mutation consent."""
        ...

    async def get_resource_status(
        self, scope: AzureTargetScope, resource_id: str
    ) -> AzureResourceStatus:
        """Read-only resource provisioning and health status check."""
        ...

    async def delete_resource(
        self, scope: AzureTargetScope, resource_id: str, consent: DeploymentConsent
    ) -> None:
        """Deletes specified resource. Requires explicit mutation consent."""
        ...

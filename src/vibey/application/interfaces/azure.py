# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""The Azure control-plane seam used by the deployment stage set."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.domain.deployment import (
    AzureTargetScope,
    DeploymentConsent,
    DeploymentSpec,
)


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


@runtime_checkable
class DeploymentSpecStore(Protocol):
    """Persists the synthesized DeploymentSpec so the execute/review stages'
    spec_provider callables have something real to read."""

    async def save_spec(self, project_id: UUID, spec: DeploymentSpec) -> None: ...


@runtime_checkable
class DeploymentConsentStore(Protocol):
    """Persists the acceptance gate's consent. Consent is digest-bound to
    one spec: a spec change after a loop-back produces a new digest, so a
    stale consent can never be silently reused."""

    async def save_consent(self, project_id: UUID, consent: DeploymentConsent) -> None: ...

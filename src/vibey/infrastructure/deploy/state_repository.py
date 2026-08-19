"""File-backed deployment spec/consent state, bound to one project's repo.

Mirrors FileDesignSpecRepository's shape but binds the repo path at
construction: the deploy handlers' existing ``spec_provider`` /
``consent_provider`` injection points are synchronous
``Callable[[UUID], X | None]``, so the loaders here are plain sync methods
(tiny local files) that bootstrap passes directly as those callables. The
writers are async, matching the store Protocols the synthesize/acceptance
handlers call.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import UUID

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


class FileDeploymentStateRepository:
    def __init__(self, repo_path: Path) -> None:
        self._root = repo_path / ".vibey" / "deploy"

    @property
    def spec_path(self) -> Path:
        return self._root / "spec.json"

    @property
    def consent_path(self) -> Path:
        return self._root / "consent.json"

    async def save_spec(self, project_id: UUID, spec: DeploymentSpec) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        raw = asdict(spec)
        raw["target_scope"]["tags"] = dict(spec.target_scope.tags)
        self.spec_path.write_text(json.dumps(raw, indent=2, default=str) + "\n")

    async def save_consent(self, project_id: UUID, consent: DeploymentConsent) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        raw = asdict(consent)
        raw["granted_at"] = consent.granted_at.isoformat()
        self.consent_path.write_text(json.dumps(raw, indent=2) + "\n")

    def load_spec(self, project_id: UUID) -> DeploymentSpec | None:
        if not self.spec_path.exists():
            return None
        raw = json.loads(self.spec_path.read_text())
        scope = raw["target_scope"]
        return DeploymentSpec(
            spec_id=str(raw["spec_id"]),
            version=str(raw["version"]),
            target_scope=AzureTargetScope(
                tenant_id=str(scope["tenant_id"]),
                subscription_id=str(scope["subscription_id"]),
                resource_group=str(scope["resource_group"]),
                environment=str(scope["environment"]),
                region=str(scope["region"]),
                tags={str(k): str(v) for k, v in scope.get("tags", {}).items()},
            ),
            identity=IdentityAuthority(
                identity_type=str(raw["identity"]["identity_type"]),
                principal_id=str(raw["identity"]["principal_id"]),
                approved_roles=tuple(str(r) for r in raw["identity"].get("approved_roles", ())),
            ),
            topology=TopologyConfig(
                service_type=str(raw["topology"]["service_type"]),
                iac_provider=str(raw["topology"]["iac_provider"]),
                sku=str(raw["topology"]["sku"]),
                instances=int(raw["topology"]["instances"]),
                ingress_enabled=bool(raw["topology"]["ingress_enabled"]),
                tls_enabled=bool(raw["topology"]["tls_enabled"]),
            ),
            recovery_policy=RecoveryPolicy(
                progressive_exposure=str(raw["recovery_policy"]["progressive_exposure"]),
                auto_rollback_on_health_failure=bool(
                    raw["recovery_policy"]["auto_rollback_on_health_failure"]
                ),
                max_rollback_attempts=int(raw["recovery_policy"]["max_rollback_attempts"]),
            ),
            verification=VerificationContract(
                health_endpoint=str(raw["verification"]["health_endpoint"]),
                smoke_tests=tuple(str(t) for t in raw["verification"].get("smoke_tests", ())),
                bake_window_seconds=int(raw["verification"]["bake_window_seconds"]),
            ),
            cost_boundary=CostBoundary(
                max_monthly_budget_usd=float(raw["cost_boundary"]["max_monthly_budget_usd"]),
                max_deployment_cost_usd=float(raw["cost_boundary"]["max_deployment_cost_usd"]),
            ),
            secret_references=tuple(str(r) for r in raw.get("secret_references", ())),
        )

    def load_consent(self, project_id: UUID) -> DeploymentConsent | None:
        if not self.consent_path.exists():
            return None
        raw = json.loads(self.consent_path.read_text())
        return DeploymentConsent(
            consent_id=str(raw["consent_id"]),
            target_scope_digest=str(raw["target_scope_digest"]),
            granted_by=str(raw["granted_by"]),
            granted_at=datetime.fromisoformat(str(raw["granted_at"])),
            explicit_mutation_authorized=bool(raw["explicit_mutation_authorized"]),
        )

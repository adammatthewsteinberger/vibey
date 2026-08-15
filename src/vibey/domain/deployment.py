"""Immutable DeploymentSpec, consent verification, and failure routing policy.

Milestone 10 task 10.2.
"""

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


@dataclass(slots=True, frozen=True)
class AzureTargetScope:
    tenant_id: str
    subscription_id: str
    resource_group: str
    environment: str
    region: str
    tags: Mapping[str, str] = field(default_factory=dict)

    def digest(self) -> str:
        raw = (
            f"{self.tenant_id}:{self.subscription_id}:{self.resource_group}:{self.environment}"
        ).encode()
        return hashlib.sha256(raw).hexdigest()


@dataclass(slots=True, frozen=True)
class IdentityAuthority:
    identity_type: str
    principal_id: str
    approved_roles: Sequence[str] = ()


@dataclass(slots=True, frozen=True)
class TopologyConfig:
    service_type: str
    iac_provider: str
    sku: str
    instances: int = 1
    ingress_enabled: bool = True
    tls_enabled: bool = True


@dataclass(slots=True, frozen=True)
class RecoveryPolicy:
    progressive_exposure: str
    auto_rollback_on_health_failure: bool = True
    max_rollback_attempts: int = 2


@dataclass(slots=True, frozen=True)
class VerificationContract:
    health_endpoint: str = "/health"
    smoke_tests: Sequence[str] = ()
    bake_window_seconds: int = 60


@dataclass(slots=True, frozen=True)
class CostBoundary:
    max_monthly_budget_usd: float
    max_deployment_cost_usd: float


@dataclass(slots=True, frozen=True)
class DeploymentSpec:
    spec_id: str
    version: str
    target_scope: AzureTargetScope
    identity: IdentityAuthority
    topology: TopologyConfig
    recovery_policy: RecoveryPolicy
    verification: VerificationContract
    cost_boundary: CostBoundary
    secret_references: Sequence[str] = ()

    def scope_digest(self) -> str:
        """Returns deterministic SHA256 hex digest of the target deployment scope."""
        return self.target_scope.digest()

    def validate(self) -> list[str]:
        """Validates that all mandatory fields are present and safe."""
        errors: list[str] = []

        if not self.spec_id.strip():
            errors.append("spec_id is required")
        if not self.version.strip():
            errors.append("version is required")

        t = self.target_scope
        if not t.tenant_id.strip():
            errors.append("tenant_id is required")
        if not t.subscription_id.strip():
            errors.append("subscription_id is required")
        if not t.resource_group.strip():
            errors.append("resource_group is required")
        if not t.environment.strip():
            errors.append("environment is required")
        if not t.region.strip():
            errors.append("region is required")

        ident = self.identity
        if not ident.identity_type.strip():
            errors.append("identity_type is required")
        if not ident.principal_id.strip():
            errors.append("principal_id is required")

        top = self.topology
        if not top.service_type.strip():
            errors.append("service_type is required")
        if not top.iac_provider.strip():
            errors.append("iac_provider is required")
        if not top.sku.strip():
            errors.append("sku is required")

        rec = self.recovery_policy
        if not rec.progressive_exposure.strip():
            errors.append("progressive_exposure is required")

        ver = self.verification
        if not ver.health_endpoint.strip():
            errors.append("health_endpoint is required")
        if ver.bake_window_seconds < 0:
            errors.append("bake_window_seconds must be >= 0")

        cost = self.cost_boundary
        if cost.max_monthly_budget_usd < 0:
            errors.append("max_monthly_budget_usd must be >= 0")
        if cost.max_deployment_cost_usd < 0:
            errors.append("max_deployment_cost_usd must be >= 0")

        for ref in self.secret_references:
            ref_lower = ref.lower().strip()
            # Allowed secret reference schemes
            valid_prefixes = (
                "@microsoft.keyvault",
                "keyvault:",
                "vault:",
                "ref:",
                "kv:",
            )
            if not any(ref_lower.startswith(prefix) for prefix in valid_prefixes):
                errors.append(
                    f"Secret reference '{ref}' appears to be a raw secret value or invalid scheme. "
                    "Must be an approved Key Vault reference URI."
                )

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0


@dataclass(slots=True, frozen=True)
class DeploymentConsent:
    consent_id: str
    target_scope_digest: str
    granted_by: str
    granted_at: datetime
    explicit_mutation_authorized: bool = True

    def matches_spec(self, spec: DeploymentSpec) -> bool:
        return self.explicit_mutation_authorized and self.target_scope_digest == spec.scope_digest()


class DeploymentFailureClass(StrEnum):
    TRANSIENT_CAPACITY = "transient_capacity"
    IDEMPOTENT_CONFLICT = "idempotent_conflict"
    CAP_EXHAUSTED = "cap_exhausted"
    MISSING_AUTHORITY = "missing_authority"
    POLICY_DENIAL = "policy_denial"
    AMBIGUOUS_CONFIGURATION = "ambiguous_configuration"
    DESTRUCTIVE_DATA_MIGRATION = "destructive_data_migration"
    RECOVERY_OUTSIDE_RUNBOOK = "recovery_outside_runbook"
    APPLICATION_DEFECT = "application_defect"


class DeploymentRoute(StrEnum):
    STAY_IN_EXECUTE = "stay_in_execute"
    ENTER_REVIEW = "enter_review"
    ROUTE_TO_DESIGN = "route_to_design"
    ROUTE_TO_DEPLOY_DESIGN = "route_to_deploy_design"


def classify_deployment_failure(failure_class: DeploymentFailureClass) -> DeploymentRoute:
    """Classifies deployment failures into deterministic routing decisions according to ADR-0013."""
    match failure_class:
        case DeploymentFailureClass.TRANSIENT_CAPACITY | DeploymentFailureClass.IDEMPOTENT_CONFLICT:
            return DeploymentRoute.STAY_IN_EXECUTE
        case DeploymentFailureClass.APPLICATION_DEFECT:
            return DeploymentRoute.ROUTE_TO_DESIGN
        case _:
            return DeploymentRoute.ENTER_REVIEW


class ChangeAction(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    NO_CHANGE = "no_change"


@dataclass(slots=True, frozen=True)
class NormalizedResourceChange:
    resource_id: str
    resource_type: str
    action: ChangeAction
    estimated_monthly_cost_usd: float = 0.0
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class PlanEvaluation:
    changes: Sequence[NormalizedResourceChange]
    total_estimated_monthly_cost_usd: float
    has_destructive_deletions: bool
    exceeds_budget: bool
    is_safe_for_automated_apply: bool
    blocking_reasons: Sequence[str]


def evaluate_iac_plan(
    changes: Sequence[NormalizedResourceChange], cost_boundary: CostBoundary
) -> PlanEvaluation:
    """Evaluates an IaC changeset against safety invariants and cost boundaries."""
    total_cost = sum(c.estimated_monthly_cost_usd for c in changes)
    destructive = any(c.action == ChangeAction.DELETE for c in changes)
    over_budget = total_cost > cost_boundary.max_monthly_budget_usd

    reasons: list[str] = []
    if destructive:
        reasons.append("Plan includes destructive resource deletions.")
    if over_budget:
        reasons.append(
            f"Estimated monthly cost (${total_cost:.2f}) exceeds monthly budget "
            f"(${cost_boundary.max_monthly_budget_usd:.2f})."
        )

    safe = (not destructive) and (not over_budget)

    return PlanEvaluation(
        changes=tuple(changes),
        total_estimated_monthly_cost_usd=total_cost,
        has_destructive_deletions=destructive,
        exceeds_budget=over_budget,
        is_safe_for_automated_apply=safe,
        blocking_reasons=tuple(reasons),
    )


class DeploymentLadderDecision(StrEnum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    HALT_AND_TRIAGE = "halt_and_triage"


@dataclass(slots=True, frozen=True)
class DeploymentAttemptRecord:
    attempt_number: int
    elapsed_seconds: float
    total_spent_usd: float
    last_failure_class: DeploymentFailureClass | None = None


def evaluate_retry_ladder(
    attempt: DeploymentAttemptRecord, spec: DeploymentSpec
) -> tuple[DeploymentLadderDecision, str]:
    """Evaluates retry and escalation ladder against attempt limits and dollar caps."""
    if attempt.total_spent_usd > spec.cost_boundary.max_deployment_cost_usd:
        return (
            DeploymentLadderDecision.HALT_AND_TRIAGE,
            f"Deployment dollar cap exceeded (${attempt.total_spent_usd:.2f} > "
            f"${spec.cost_boundary.max_deployment_cost_usd:.2f})",
        )

    if attempt.elapsed_seconds > 1800.0:
        return (
            DeploymentLadderDecision.HALT_AND_TRIAGE,
            f"Deployment timeout elapsed cap exceeded ({attempt.elapsed_seconds:.1f}s > 1800.0s)",
        )

    max_allowed_attempts = spec.recovery_policy.max_rollback_attempts + 1
    if attempt.attempt_number >= max_allowed_attempts:
        return (
            DeploymentLadderDecision.HALT_AND_TRIAGE,
            f"Max deployment attempts exceeded "
            f"({attempt.attempt_number} >= {max_allowed_attempts})",
        )

    if attempt.last_failure_class in (
        DeploymentFailureClass.TRANSIENT_CAPACITY,
        DeploymentFailureClass.IDEMPOTENT_CONFLICT,
    ):
        return (
            DeploymentLadderDecision.RETRY,
            f"Transient failure ({attempt.last_failure_class}) eligible for retry with backoff",
        )

    if spec.recovery_policy.auto_rollback_on_health_failure:
        return (
            DeploymentLadderDecision.ROLLBACK,
            "Health failure encountered; initiating automated rollback",
        )

    return (
        DeploymentLadderDecision.HALT_AND_TRIAGE,
        "Non-retryable failure requires human triage in review",
    )


class ExposureType(StrEnum):
    REVISION = "revision"
    SLOT = "slot"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    STAMP = "stamp"


class RecoveryActionType(StrEnum):
    ROLLBACK = "rollback"
    ROLL_FORWARD = "roll_forward"
    FALLBACK = "fallback"


@dataclass(slots=True, frozen=True)
class RecoveryAction:
    action_type: RecoveryActionType
    target_revision_or_slot: str
    initiated_reason: str
    max_attempts: int = 2


def evaluate_exposure_step(
    current_percent: int,
    *,
    is_healthy: bool,
    policy: RecoveryPolicy,
    step_size: int = 25,
) -> tuple[int, RecoveryAction | None]:
    """Computes next traffic percentage or required policy-bound recovery action."""
    if not is_healthy:
        if policy.auto_rollback_on_health_failure:
            return (
                0,
                RecoveryAction(
                    action_type=RecoveryActionType.ROLLBACK,
                    target_revision_or_slot="previous_stable",
                    initiated_reason="Health check degradation during rollout",
                ),
            )
        return (
            current_percent,
            RecoveryAction(
                action_type=RecoveryActionType.FALLBACK,
                target_revision_or_slot="hold",
                initiated_reason="Health check degradation with auto-rollback disabled",
            ),
        )

    next_percent = min(100, current_percent + step_size)
    return (next_percent, None)


class VerificationDimension(StrEnum):
    CONVERGENCE = "convergence"
    HEALTH = "health"
    SMOKE = "smoke"
    BAKE_WINDOW = "bake_window"


@dataclass(slots=True, frozen=True)
class VerificationResult:
    passed: bool
    dimension_results: Mapping[str, bool]
    failed_dimension: VerificationDimension | None = None
    failure_reason: str | None = None


def evaluate_verification_contract(
    contract: VerificationContract,
    *,
    convergence_succeeded: bool,
    health_status_code: int,
    smoke_commands_passed: bool,
    bake_window_errors_count: int,
) -> VerificationResult:
    """Evaluates all 4 dimensions of the deployment runtime verification contract."""
    dimension_results = {
        "convergence": convergence_succeeded,
        "health": 200 <= health_status_code < 300,
        "smoke": smoke_commands_passed,
        "bake_window": bake_window_errors_count == 0,
    }

    if not convergence_succeeded:
        return VerificationResult(
            passed=False,
            dimension_results=dimension_results,
            failed_dimension=VerificationDimension.CONVERGENCE,
            failure_reason="Convergence failed: resource provisioning state is not Succeeded",
        )

    if not (200 <= health_status_code < 300):
        return VerificationResult(
            passed=False,
            dimension_results=dimension_results,
            failed_dimension=VerificationDimension.HEALTH,
            failure_reason=(
                f"Health check at {contract.health_endpoint} failed with HTTP status "
                f"{health_status_code}"
            ),
        )

    if not smoke_commands_passed:
        return VerificationResult(
            passed=False,
            dimension_results=dimension_results,
            failed_dimension=VerificationDimension.SMOKE,
            failure_reason="One or more smoke/acceptance verification commands failed",
        )

    if bake_window_errors_count > 0:
        return VerificationResult(
            passed=False,
            dimension_results=dimension_results,
            failed_dimension=VerificationDimension.BAKE_WINDOW,
            failure_reason=(
                f"Bake window ({contract.bake_window_seconds}s) recorded "
                f"{bake_window_errors_count} error occurrences"
            ),
        )

    return VerificationResult(
        passed=True,
        dimension_results=dimension_results,
        failed_dimension=None,
        failure_reason=None,
    )

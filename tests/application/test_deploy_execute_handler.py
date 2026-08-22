# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from tests.application.fakes import FakeJobRepository, make_job
from vibey.application.azure_port import (
    AzureDiscoveryResult,
    AzureExecutionResult,
    AzureResourceStatus,
)
from vibey.application.deploy_execute_handler import (
    DeployExecuteHandler,
    DeployStep,
)
from vibey.application.worker import Failure, Success
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
from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event
from vibey.domain.phase import Phase

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class FakeClock:
    def now(self) -> datetime:
        return NOW


class FakeDeployLedger:
    def __init__(self) -> None:
        self.events: list[LedgerEvent] = []

    async def all_for_project(self, project_id: UUID) -> Sequence[LedgerEvent]:
        return [e for e in self.events if e.project_id == project_id]

    async def append_event(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        kind: EventKind,
        payload: Mapping[str, object],
    ) -> None:
        seq = len(self.events) + 1
        self.events.append(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=cycle,
                phase=Phase.DEPLOY_EXECUTE,
                seq=seq,
                kind=kind,
                engine_id=EngineId.CLAUDELOOP,
                job_id=job_id,
                causation_id=None,
                correlation_id=uuid4(),
                provenance=Provenance.TRUSTED,
                produced_at=NOW,
                payload=dict(payload),
                digest=digest_event(payload),
            )
        )


class FakeProjectTransitioner:
    def __init__(self) -> None:
        self.transitions: list[tuple[UUID, Phase, Phase]] = []

    async def transition(
        self, project_id: UUID, *, expected: Phase, to: Phase, cycle: int | None = None
    ) -> Any:
        self.transitions.append((project_id, expected, to))


class FakeAzureClient:
    def __init__(
        self,
        *,
        fail_at_step: DeployStep | None = None,
        failure_type: str = "error",
    ) -> None:
        self.fail_at_step = fail_at_step
        self.failure_type = failure_type
        self.steps_run: list[DeployStep] = []

    async def discover_environment(self, scope: AzureTargetScope) -> AzureDiscoveryResult:
        self.steps_run.append(DeployStep.DISCOVER)
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
        self.steps_run.append(DeployStep.APPLY)
        if self.fail_at_step == DeployStep.APPLY:
            raise RuntimeError(f"Azure Apply Failure: {self.failure_type}")
        return AzureExecutionResult(
            deployment_id=f"dep-{spec.spec_id}",
            provisioning_state="Succeeded",
            outputs={"endpoint": f"https://{spec.spec_id}.azurecontainerapps.io"},
            applied_at=NOW,
        )

    async def get_resource_status(
        self, scope: AzureTargetScope, resource_id: str
    ) -> AzureResourceStatus:
        self.steps_run.append(DeployStep.VERIFY)
        if self.fail_at_step == DeployStep.VERIFY:
            return AzureResourceStatus(resource_id, "Failed", "Degraded")
        return AzureResourceStatus(resource_id, "Succeeded", "Healthy")

    async def delete_resource(
        self, scope: AzureTargetScope, resource_id: str, consent: DeploymentConsent
    ) -> None:
        pass


def _sample_spec() -> DeploymentSpec:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy("revision", True)
    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(100.0, 10.0)
    return DeploymentSpec(
        spec_id="spec-1",
        version="1.0",
        target_scope=target,
        identity=identity,
        topology=topology,
        recovery_policy=recovery,
        verification=verification,
        cost_boundary=cost,
    )


@pytest.mark.asyncio
async def test_deploy_execute_clean_run_to_review() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_EXECUTE,
        kind="deploy.execute",
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("status") == "verified"
    assert len(projects.transitions) == 1
    assert projects.transitions[0][1] == Phase.DEPLOY_EXECUTE
    assert projects.transitions[0][2] == Phase.DEPLOY_REVIEW
    # Enqueued deploy.demo for Phase 6
    enqueued = list(jobs._jobs.values())
    assert any(j.kind == "deploy.demo" for j in enqueued)


@pytest.mark.asyncio
async def test_deploy_execute_failure_pauses_to_review_triage() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient(fail_at_step=DeployStep.APPLY, failure_type="policy_denial")
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_EXECUTE,
        kind="deploy.execute",
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Failure)
    # Transition to DEPLOY_REVIEW for triage
    assert len(projects.transitions) == 1
    assert projects.transitions[0][2] == Phase.DEPLOY_REVIEW
    enqueued = list(jobs._jobs.values())
    assert any(j.kind == "deploy.triage" for j in enqueued)


@pytest.mark.asyncio
async def test_deploy_execute_edge_cases() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    # Wrong job kind
    handler = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )
    base_job = make_job(uuid4())
    wrong_job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_EXECUTE,
        kind="other.kind",
    )
    assert isinstance(await handler.handle(wrong_job), Failure)

    # Missing spec
    handler_no_spec = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        clock=FakeClock(),
        spec_provider=lambda _pid: None,
        consent_provider=lambda _pid: consent,
    )
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_EXECUTE,
        kind="deploy.execute",
    )
    assert isinstance(await handler_no_spec.handle(job), Failure)

    # Missing consent
    handler_no_consent = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: None,
    )
    assert isinstance(await handler_no_consent.handle(job), Failure)

    # Verification failure
    client_verify_fail = FakeAzureClient(fail_at_step=DeployStep.VERIFY)
    handler_verify_fail = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client_verify_fail,
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )
    outcome_vf = await handler_verify_fail.handle(job)
    assert isinstance(outcome_vf, Failure)


@pytest.mark.asyncio
async def test_deploy_execute_skips_transition_without_transition_method() -> None:
    """Success path with projects=object() covers hasattr False at line 107."""
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=object(),
        azure_client=client,
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_EXECUTE,
        kind="deploy.execute",
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("status") == "verified"
    enqueued = list(jobs._jobs.values())
    assert any(j.kind == "deploy.demo" for j in enqueued)


@pytest.mark.asyncio
async def test_deploy_execute_failure_skips_transition_without_transition_method() -> None:
    """Failure path with projects=object() covers hasattr False at line 150."""
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    client = FakeAzureClient(fail_at_step=DeployStep.APPLY, failure_type="policy_denial")
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=object(),
        azure_client=client,
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_EXECUTE,
        kind="deploy.execute",
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Failure)
    enqueued = list(jobs._jobs.values())
    assert any(j.kind == "deploy.triage" for j in enqueued)

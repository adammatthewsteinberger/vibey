# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
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
from vibey.application.deploy_review_routing import (
    DeployReviewAction,
    DeployReviewRoutingHandler,
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
                phase=Phase.DEPLOY_REVIEW,
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
    def __init__(self) -> None:
        self.deleted_resources: list[str] = []

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
        return AzureExecutionResult("dep-1", "Succeeded", {}, NOW)

    async def get_resource_status(
        self, scope: AzureTargetScope, resource_id: str
    ) -> AzureResourceStatus:
        return AzureResourceStatus(resource_id, "Succeeded", "Healthy")

    async def delete_resource(
        self, scope: AzureTargetScope, resource_id: str, consent: DeploymentConsent
    ) -> None:
        self.deleted_resources.append(resource_id)


def _sample_spec() -> DeploymentSpec:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy("revision", True)
    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(100.0, 10.0)
    return DeploymentSpec("spec-1", "1.0", target, identity, topology, recovery, verification, cost)


@pytest.mark.asyncio
async def test_review_routing_approve_transitions_to_done() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployReviewRoutingHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind", "payload"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="deploy.route",
        payload={"action": DeployReviewAction.APPROVE.value},
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert len(projects.transitions) == 1
    assert projects.transitions[0] == (job.project_id, Phase.DEPLOY_REVIEW, Phase.DONE)


@pytest.mark.asyncio
async def test_review_routing_loop_design_transitions_to_phase4() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployReviewRoutingHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind", "payload"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="deploy.route",
        payload={"action": DeployReviewAction.LOOP_DESIGN.value},
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert len(projects.transitions) == 1
    assert projects.transitions[0] == (job.project_id, Phase.DEPLOY_REVIEW, Phase.DEPLOY_DESIGN)
    enqueued = list(jobs._jobs.values())
    assert any(j.kind == "deploy.interview" for j in enqueued)


@pytest.mark.asyncio
async def test_review_routing_retry_execute_transitions_to_phase5() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployReviewRoutingHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind", "payload"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="deploy.route",
        payload={"action": DeployReviewAction.RETRY_EXECUTE.value},
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert len(projects.transitions) == 1
    assert projects.transitions[0] == (job.project_id, Phase.DEPLOY_REVIEW, Phase.DEPLOY_EXECUTE)
    enqueued = list(jobs._jobs.values())
    assert any(j.kind == "deploy.execute" for j in enqueued)


@pytest.mark.asyncio
async def test_review_routing_loop_code_cleans_up_and_transitions_to_plan() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployReviewRoutingHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind", "payload"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="deploy.route",
        payload={"action": DeployReviewAction.LOOP_CODE_FIX.value, "cleanup_ephemeral": True},
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert len(client.deleted_resources) == 1
    assert len(projects.transitions) == 1
    assert projects.transitions[0] == (job.project_id, Phase.DEPLOY_REVIEW, Phase.DESIGN)


@pytest.mark.asyncio
async def test_deploy_review_routing_edge_cases() -> None:
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    client = FakeAzureClient()
    spec = _sample_spec()
    consent = DeploymentConsent("c-1", spec.scope_digest(), "user", NOW, True)

    handler = DeployReviewRoutingHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=client,
        spec_provider=lambda _pid: spec,
        consent_provider=lambda _pid: consent,
    )

    base_job = make_job(uuid4())
    wrong_job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind", "payload"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="wrong.kind",
        payload={},
    )
    assert isinstance(await handler.handle(wrong_job), Failure)

    # Abort action
    abort_job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind", "payload"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="deploy.route",
        payload={"action": DeployReviewAction.ABORT.value},
    )
    outcome_abort = await handler.handle(abort_job)
    assert isinstance(outcome_abort, Success)
    assert outcome_abort.result.get("target_phase") == Phase.DONE.name


@pytest.mark.asyncio
async def test_review_routing_skips_transition_when_projects_lacks_method() -> None:
    """When projects is a plain object without a transition method,
    hasattr checks are False and the handler still succeeds."""
    ledger = FakeDeployLedger()
    jobs = FakeJobRepository()
    client = FakeAzureClient()

    handler = DeployReviewRoutingHandler(
        ledger=ledger,
        jobs=jobs,
        projects=object(),
        azure_client=client,
    )

    base_job = make_job(uuid4())

    for action, expected_status in [
        (DeployReviewAction.APPROVE.value, "approved"),
        (DeployReviewAction.LOOP_DESIGN.value, "loop_design"),
        (DeployReviewAction.RETRY_EXECUTE.value, "retry_execute"),
        (DeployReviewAction.ABORT.value, DeployReviewAction.ABORT.value),
    ]:
        job = base_job.__class__(
            **{
                k: getattr(base_job, k)
                for k in base_job.__dataclass_fields__
                if k not in {"phase", "kind", "payload"}
            },
            phase=Phase.DEPLOY_REVIEW,
            kind="deploy.route",
            payload={"action": action},
        )
        outcome = await handler.handle(job)
        assert isinstance(outcome, Success)
        assert outcome.result.get("status") == expected_status

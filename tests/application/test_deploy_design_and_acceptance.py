from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from tests.application.fakes import (
    FakeHumanGateRepository,
    FakeJobRepository,
    make_job,
)
from vibey.application.deploy_acceptance_handler import DeployAcceptanceHandler
from vibey.application.deploy_design_handler import DeployInterviewHandler, DeploySynthesizeHandler
from vibey.application.worker import Failure, Park, Success
from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
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
                phase=Phase.DEPLOY_DESIGN,
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


def _valid_spec() -> DeploymentSpec:
    target = AzureTargetScope(
        tenant_id="tenant-123",
        subscription_id="sub-456",
        resource_group="rg-vibey-dev",
        environment="dev",
        region="eastus",
    )
    identity = IdentityAuthority(
        identity_type="workload_identity_oidc",
        principal_id="principal-789",
        approved_roles=("Contributor",),
    )
    topology = TopologyConfig(
        service_type="container_app",
        iac_provider="bicep",
        sku="Standard_B1s",
    )
    recovery = RecoveryPolicy(
        progressive_exposure="revision",
        auto_rollback_on_health_failure=True,
    )
    verification = VerificationContract(
        health_endpoint="/health",
        smoke_tests=("curl -f https://example.com/health",),
        bake_window_seconds=60,
    )
    cost = CostBoundary(
        max_monthly_budget_usd=100.0,
        max_deployment_cost_usd=10.0,
    )
    return DeploymentSpec(
        spec_id="spec-dep-1",
        version="1.0.0",
        target_scope=target,
        identity=identity,
        topology=topology,
        recovery_policy=recovery,
        verification=verification,
        cost_boundary=cost,
        secret_references=(
            "@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/db/)",
        ),
    )


@pytest.mark.asyncio
async def test_deploy_interview_handler_flow() -> None:
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    clock = FakeClock()

    handler = DeployInterviewHandler(ledger=ledger, gates=gates, clock=clock)
    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_DESIGN,
        kind="deploy.interview",
    )

    # Initial pass raises human gate for interview stage
    outcome = await handler.handle(job)
    assert isinstance(outcome, Park)

    # Answering the gate appends answer to ledger and completes step
    gate = await gates.latest_for_job(job.id)
    assert gate is not None
    await gates.answer(
        gate.gate_id,
        answer={"stage": 1, "target": "container_app", "environment": "dev"},
        answered_by="user",
    )

    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Success)
    assert any(e.kind == EventKind.ANSWER_GIVEN for e in ledger.events)


@pytest.mark.asyncio
async def test_deploy_synthesize_handler() -> None:
    ledger = FakeDeployLedger()
    clock = FakeClock()

    handler = DeploySynthesizeHandler(ledger=ledger, clock=clock)
    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_DESIGN,
        kind="deploy.synthesize",
    )

    outcome = await handler.handle(job)
    assert isinstance(outcome, Success)
    assert outcome.result.get("status") == "synthesized"
    assert any(e.kind == EventKind.ARTIFACT_PRODUCED for e in ledger.events)


@pytest.mark.asyncio
async def test_deploy_acceptance_handler_success() -> None:
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    clock = FakeClock()

    spec = _valid_spec()
    handler = DeployAcceptanceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
        spec_provider=lambda _pid: spec,
    )
    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_DESIGN,
        kind="deploy.spec",
    )

    # Initial pass raises acceptance gate
    outcome = await handler.handle(job)
    assert isinstance(outcome, Park)

    # User accepts deployment specification & grants mutation consent
    gate = await gates.latest_for_job(job.id)
    assert gate is not None
    await gates.answer(
        gate.gate_id,
        answer={"verdict": "accept", "explicit_mutation_authorized": True},
        answered_by="user",
    )

    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Success)
    assert outcome2.result.get("verdict") == "accepted"
    assert len(projects.transitions) == 1
    assert projects.transitions[0][1] == Phase.DEPLOY_DESIGN
    assert projects.transitions[0][2] == Phase.DEPLOY_EXECUTE
    assert len(jobs._jobs) == 1
    enqueued_job = next(iter(jobs._jobs.values()))
    assert enqueued_job.kind == "deploy.execute"


@pytest.mark.asyncio
async def test_deploy_acceptance_handler_rejections() -> None:
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    clock = FakeClock()

    handler = DeployAcceptanceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
        spec_provider=lambda _pid: None,
    )
    base_job = make_job(uuid4())
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_DESIGN,
        kind="deploy.spec",
    )

    await handler.handle(job)
    gate = await gates.latest_for_job(job.id)
    assert gate is not None

    # Reject verdict
    await gates.answer(gate.gate_id, answer={"verdict": "reject"}, answered_by="user")
    outcome_reject = await handler.handle(job)
    assert isinstance(outcome_reject, Failure)

    # Missing spec with accept verdict
    await gates.answer(
        gate.gate_id,
        answer={"verdict": "accept", "explicit_mutation_authorized": True},
        answered_by="user",
    )
    outcome_no_spec = await handler.handle(job)
    assert isinstance(outcome_no_spec, Failure)


@pytest.mark.asyncio
async def test_deploy_handlers_edge_cases() -> None:
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    clock = FakeClock()

    # Wrong kinds
    interview_handler = DeployInterviewHandler(ledger=ledger, gates=gates, clock=clock)
    synthesize_handler = DeploySynthesizeHandler(ledger=ledger, clock=clock)
    invalid_spec = DeploymentSpec(
        spec_id="",
        version="",
        target_scope=AzureTargetScope("", "", "", "", ""),
        identity=IdentityAuthority("", "", ()),
        topology=TopologyConfig("", "", ""),
        recovery_policy=RecoveryPolicy("", False),
        verification=VerificationContract("", (), -1),
        cost_boundary=CostBoundary(-1, -1),
    )
    acceptance_handler = DeployAcceptanceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
        spec_provider=lambda _pid: invalid_spec,
    )

    base_job = make_job(uuid4())
    wrong_job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_DESIGN,
        kind="other.kind",
    )

    assert isinstance(await interview_handler.handle(wrong_job), Failure)
    assert isinstance(await synthesize_handler.handle(wrong_job), Failure)
    assert isinstance(await acceptance_handler.handle(wrong_job), Failure)

    # Gate raised but answer is None (re-parks)
    interview_job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_DESIGN,
        kind="deploy.interview",
    )
    # First call raises gate
    outcome_park1 = await interview_handler.handle(interview_job)
    assert isinstance(outcome_park1, Park)
    # Second call without answering still parks
    outcome_park2 = await interview_handler.handle(interview_job)
    assert isinstance(outcome_park2, Park)

    # Acceptance handler with gate raised and answer is None
    spec_job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_DESIGN,
        kind="deploy.spec",
    )
    await acceptance_handler.handle(spec_job)
    outcome_acc_park2 = await acceptance_handler.handle(spec_job)
    assert isinstance(outcome_acc_park2, Park)

    # Spec validation failure
    gate = await gates.latest_for_job(spec_job.id)
    assert gate is not None
    await gates.answer(
        gate.gate_id,
        answer={"verdict": "accept", "explicit_mutation_authorized": True},
        answered_by="user",
    )
    outcome_invalid_spec = await acceptance_handler.handle(spec_job)
    assert isinstance(outcome_invalid_spec, Failure)

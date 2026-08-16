from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from tests.application.fakes import FakeHumanGateRepository, make_job
from vibey.application.deploy_review_handler import (
    DeployReviewDemoHandler,
    DeployReviewTriageHandler,
)
from vibey.application.worker import Failure, Park, Success
from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
    DeploymentFailureClass,
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
    def __init__(self, events: Sequence[LedgerEvent] | None = None) -> None:
        self.events: list[LedgerEvent] = list(events or [])

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


def _sample_spec() -> DeploymentSpec:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-1", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy("revision", True)
    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(100.0, 10.0)
    return DeploymentSpec("spec-1", "1.0", target, identity, topology, recovery, verification, cost)


@pytest.mark.asyncio
async def test_deploy_review_demo_creates_gate_and_handles_answer() -> None:
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    spec = _sample_spec()

    # Pre-populate artifact produced event from execute phase
    dep_id = uuid4()
    await ledger.append_event(
        project_id=dep_id,
        cycle=1,
        job_id=uuid4(),
        kind=EventKind.ARTIFACT_PRODUCED,
        payload={
            "artifact_type": "deployment_verification",
            "deployment_id": "dep-123",
            "outputs": {"endpoint": "https://app.azurecontainerapps.io"},
        },
    )

    handler = DeployReviewDemoHandler(
        ledger=ledger,
        human_gates=gates,
        spec_provider=lambda _pid: spec,
    )

    base_job = make_job(dep_id)
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="deploy.demo",
    )

    # 1. Unanswered -> Park
    outcome1 = await handler.handle(job)
    assert isinstance(outcome1, Park)
    assert "https://app.azurecontainerapps.io" in outcome1.request.prompt

    # 2. Gate raised but unanswered
    gate = await gates.latest_for_job(job.id)
    assert gate is not None
    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Park)

    # 3. Answer gate -> Success
    await gates.answer(gate.gate_id, answer={"approved": True}, answered_by="user")
    outcome3 = await handler.handle(job)
    assert isinstance(outcome3, Success)
    assert outcome3.result.get("status") == "demo_approved"


@pytest.mark.asyncio
async def test_deploy_review_triage_creates_gate_and_handles_answer() -> None:
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    spec = _sample_spec()

    # Pre-populate finding event from execute phase
    proj_id = uuid4()
    await ledger.append_event(
        project_id=proj_id,
        cycle=1,
        job_id=uuid4(),
        kind=EventKind.FINDING_RAISED,
        payload={
            "finding_id": "finding-1",
            "failure_class": DeploymentFailureClass.POLICY_DENIAL.value,
            "error": "Azure Policy disallows sku Standard_B1s",
        },
    )

    handler = DeployReviewTriageHandler(
        ledger=ledger,
        human_gates=gates,
        spec_provider=lambda _pid: spec,
    )

    base_job = make_job(proj_id)
    job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="deploy.triage",
    )

    # 1. Unanswered -> Park
    outcome1 = await handler.handle(job)
    assert isinstance(outcome1, Park)
    prompt = outcome1.request.prompt
    assert "POLICY_DENIAL" in prompt or "policy" in prompt.lower()
    assert "remediation" in prompt.lower() or "options" in prompt.lower()

    # 2. Gate raised but unanswered
    gate = await gates.latest_for_job(job.id)
    assert gate is not None
    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Park)

    # 3. Answer gate -> Success
    await gates.answer(gate.gate_id, answer={"action": "LOOP_DEPLOY_DESIGN"}, answered_by="user")
    outcome3 = await handler.handle(job)
    assert isinstance(outcome3, Success)
    assert outcome3.result.get("status") == "triage_answered"
    assert outcome3.result.get("failure_class") == DeploymentFailureClass.POLICY_DENIAL.value


@pytest.mark.asyncio
async def test_deploy_review_edge_cases() -> None:
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    handler_demo = DeployReviewDemoHandler(ledger=ledger, human_gates=gates)
    handler_triage = DeployReviewTriageHandler(ledger=ledger, human_gates=gates)

    base_job = make_job(uuid4())
    wrong_job = base_job.__class__(
        **{
            k: getattr(base_job, k)
            for k in base_job.__dataclass_fields__
            if k not in {"phase", "kind"}
        },
        phase=Phase.DEPLOY_REVIEW,
        kind="wrong.kind",
    )

    assert isinstance(await handler_demo.handle(wrong_job), Failure)
    assert isinstance(await handler_triage.handle(wrong_job), Failure)

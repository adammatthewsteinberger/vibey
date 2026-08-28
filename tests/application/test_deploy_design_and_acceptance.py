# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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


@pytest.mark.asyncio
async def test_deploy_acceptance_skips_transition_without_transition_method() -> None:
    """When projects is a plain object without transition, the handler still succeeds."""
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    jobs = FakeJobRepository()
    clock = FakeClock()

    spec = _valid_spec()
    handler = DeployAcceptanceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=object(),
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

    outcome = await handler.handle(job)
    assert isinstance(outcome, Park)

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
    assert len(jobs._jobs) >= 1


@pytest.mark.asyncio
async def test_deploy_interview_reparks_when_gate_unanswered() -> None:
    """Covers deploy_design_handler.py line 45: gate.answer is None re-parks."""
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

    outcome1 = await handler.handle(job)
    assert isinstance(outcome1, Park)
    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Park)


@pytest.mark.asyncio
async def test_deploy_acceptance_reparks_when_gate_unanswered() -> None:
    """Covers deploy_acceptance_handler.py line 58: gate.answer is None re-parks."""
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
        spec_provider=lambda _pid: _valid_spec(),
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

    outcome1 = await handler.handle(job)
    assert isinstance(outcome1, Park)
    outcome2 = await handler.handle(job)
    assert isinstance(outcome2, Park)


@pytest.mark.asyncio
async def test_deploy_acceptance_invalid_spec_returns_failure() -> None:
    """Covers deploy_acceptance_handler.py line 83: invalid spec validation."""
    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    jobs = FakeJobRepository()
    projects = FakeProjectTransitioner()
    clock = FakeClock()

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
    handler = DeployAcceptanceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
        spec_provider=lambda _pid: invalid_spec,
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
    await gates.answer(
        gate.gate_id,
        answer={"verdict": "accept", "explicit_mutation_authorized": True},
        answered_by="user",
    )
    outcome = await handler.handle(job)
    assert isinstance(outcome, Failure)


@pytest.mark.asyncio
async def test_deploy_interview_with_jobs_enqueues_synthesize() -> None:
    from dataclasses import replace

    from tests.application.fakes import FakeJobRepository

    ledger = FakeDeployLedger()
    gates = FakeHumanGateRepository()
    jobs = FakeJobRepository()
    handler = DeployInterviewHandler(ledger=ledger, gates=gates, clock=FakeClock(), jobs=jobs)
    job = replace(make_job(uuid4()), phase=Phase.DEPLOY_DESIGN, kind="deploy.interview")

    first = await handler.handle(job)
    assert isinstance(first, Park)
    gate = await gates.latest_for_job(job.id)
    assert gate is not None
    await gates.answer(gate.gate_id, answer={"choice": "accept_defaults"}, answered_by="user")

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    synth = [j for j in jobs._jobs.values() if j.kind == "deploy.synthesize"]
    assert len(synth) == 1
    assert synth[0].phase is Phase.DEPLOY_DESIGN


@pytest.mark.asyncio
async def test_deploy_synthesize_with_jobs_enqueues_spec() -> None:
    from dataclasses import replace

    from tests.application.fakes import FakeJobRepository

    jobs = FakeJobRepository()
    handler = DeploySynthesizeHandler(ledger=FakeDeployLedger(), clock=FakeClock(), jobs=jobs)
    job = replace(make_job(uuid4()), phase=Phase.DEPLOY_DESIGN, kind="deploy.synthesize")

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    spec_jobs = [j for j in jobs._jobs.values() if j.kind == "deploy.spec"]
    assert len(spec_jobs) == 1
    assert spec_jobs[0].phase is Phase.DEPLOY_DESIGN


class FakeSpecStore:
    def __init__(self) -> None:
        self.saved: list[object] = []

    async def save_spec(self, project_id, spec):  # type: ignore[no-untyped-def]
        self.saved.append(spec)


class FakeConsentStore:
    def __init__(self) -> None:
        self.saved: list[object] = []

    async def save_consent(self, project_id, consent):  # type: ignore[no-untyped-def]
        self.saved.append(consent)


@pytest.mark.asyncio
async def test_synthesize_builds_and_persists_a_valid_spec_from_answers() -> None:
    from dataclasses import replace

    from vibey.domain.ledger import LedgerEvent

    interview_answer = {"environment": "prod", "region": "westeurope", "sku": "dedicated"}
    job = replace(make_job(uuid4()), phase=Phase.DEPLOY_DESIGN, kind="deploy.synthesize")
    ledger = FakeDeployLedger()
    payload = {"stage": "deploy_elicitation", "answer": interview_answer}
    ledger.events.append(
        LedgerEvent(
            event_id=uuid4(),
            project_id=job.project_id,
            seq=1,
            cycle=1,
            phase=Phase.DEPLOY_DESIGN,
            kind=EventKind.ANSWER_GIVEN,
            engine_id=None,
            job_id=uuid4(),
            causation_id=None,
            correlation_id=uuid4(),
            provenance=Provenance.TRUSTED,
            produced_at=datetime(2026, 8, 19, tzinfo=UTC),
            payload=payload,
            digest=digest_event(payload),
        )
    )
    store = FakeSpecStore()
    handler = DeploySynthesizeHandler(ledger=ledger, clock=FakeClock(), jobs=None, spec_store=store)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert len(store.saved) == 1
    spec = store.saved[0]
    assert spec.target_scope.environment == "prod"
    assert spec.target_scope.region == "westeurope"
    assert spec.topology.sku == "dedicated"
    assert spec.validate() == []


@pytest.mark.asyncio
async def test_synthesize_rejects_answers_that_produce_an_invalid_spec() -> None:
    from dataclasses import replace

    from vibey.domain.ledger import LedgerEvent

    bad_answer = {"tenant_id": "   "}
    job = replace(make_job(uuid4()), phase=Phase.DEPLOY_DESIGN, kind="deploy.synthesize")
    ledger = FakeDeployLedger()
    payload = {"stage": "deploy_elicitation", "answer": bad_answer}
    ledger.events.append(
        LedgerEvent(
            event_id=uuid4(),
            project_id=job.project_id,
            seq=1,
            cycle=1,
            phase=Phase.DEPLOY_DESIGN,
            kind=EventKind.ANSWER_GIVEN,
            engine_id=None,
            job_id=uuid4(),
            causation_id=None,
            correlation_id=uuid4(),
            provenance=Provenance.TRUSTED,
            produced_at=datetime(2026, 8, 19, tzinfo=UTC),
            payload=payload,
            digest=digest_event(payload),
        )
    )
    store = FakeSpecStore()
    handler = DeploySynthesizeHandler(ledger=ledger, clock=FakeClock(), spec_store=store)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Failure)
    assert "invalid" in outcome.detail
    assert store.saved == []


@pytest.mark.asyncio
async def test_acceptance_persists_the_consent_it_grants() -> None:
    from dataclasses import replace

    from tests.application.fakes import FakeJobRepository

    gates = FakeHumanGateRepository()
    consent_store = FakeConsentStore()
    spec = _valid_spec()
    handler = DeployAcceptanceHandler(
        ledger=FakeDeployLedger(),
        gates=gates,
        jobs=FakeJobRepository(),
        projects=object(),
        clock=FakeClock(),
        spec_provider=lambda _pid: spec,
        consent_store=consent_store,
    )
    job = replace(make_job(uuid4()), phase=Phase.DEPLOY_DESIGN, kind="deploy.accept")

    first = await handler.handle(job)
    assert not isinstance(first, Success)
    gate = await gates.latest_for_job(job.id)
    assert gate is not None
    await gates.answer(
        gate.gate_id,
        answer={"verdict": "accept", "explicit_mutation_authorized": True},
        answered_by="user",
    )

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert len(consent_store.saved) == 1
    consent = consent_store.saved[0]
    assert consent.target_scope_digest == spec.scope_digest()
    assert consent.matches_spec(spec) is True


@pytest.mark.asyncio
async def test_synthesize_skips_foreign_stages_and_non_mapping_answers() -> None:
    from dataclasses import replace

    from vibey.domain.ledger import LedgerEvent

    job = replace(make_job(uuid4()), phase=Phase.DEPLOY_DESIGN, kind="deploy.synthesize")
    ledger = FakeDeployLedger()
    for seq, payload in enumerate(
        (
            {"stage": "design_interview", "answer": {"unrelated": "x"}},
            {"stage": "deploy_elicitation", "answer": "accept_defaults"},
        ),
        start=1,
    ):
        ledger.events.append(
            LedgerEvent(
                event_id=uuid4(),
                project_id=job.project_id,
                seq=seq,
                cycle=1,
                phase=Phase.DEPLOY_DESIGN,
                kind=EventKind.ANSWER_GIVEN,
                engine_id=None,
                job_id=uuid4(),
                causation_id=None,
                correlation_id=uuid4(),
                provenance=Provenance.TRUSTED,
                produced_at=datetime(2026, 8, 19, tzinfo=UTC),
                payload=payload,
                digest=digest_event(payload),
            )
        )
    store = FakeSpecStore()
    handler = DeploySynthesizeHandler(ledger=ledger, clock=FakeClock(), spec_store=store)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert len(store.saved) == 1
    # neither event contributed answers, so the defaults stand
    assert store.saved[0].target_scope.environment == "dev"

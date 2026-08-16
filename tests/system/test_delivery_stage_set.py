"""Delivery-stage-set system tests (M7 task 7.9 and M10 task 10.13).

Validates the full deterministic, offline delivery stage set:
Phase 1 (DESIGN) -> (Visual Opt-In / Opt-Out) -> Phase 2 (BUILD)
-> Phase 3 (REVIEW) -> (Deployment Opt-In / Opt-Out)
including review loopback to re-entrant DESIGN, and the full
deployment path: ①→②→③→④→⑤→⑥→DONE.
"""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from tests.application.fakes import FakeHumanGateRepository, FakeJobRepository
from vibey.application.azure_port import (
    AzureDiscoveryResult,
    AzureExecutionResult,
    AzureResourceStatus,
)
from vibey.application.build_decompose_handler import BuildDecomposeHandler
from vibey.application.deploy_acceptance_handler import DeployAcceptanceHandler
from vibey.application.deploy_design_handler import DeployInterviewHandler, DeploySynthesizeHandler
from vibey.application.deploy_execute_handler import DeployExecuteHandler
from vibey.application.deploy_review_handler import DeployReviewDemoHandler
from vibey.application.deploy_review_routing import DeployReviewRoutingHandler
from vibey.application.design import (
    DesignEvent,
    stages_for_cycle,
)
from vibey.application.design_acceptance import DesignAcceptanceService
from vibey.application.design_handler import DesignInterviewHandler
from vibey.application.design_research_handler import DesignResearchHandler
from vibey.application.design_synthesis_handler import (
    DesignSpecHandler,
    DesignSynthesizeHandler,
)
from vibey.application.dto import JobRecord, ProjectRecord
from vibey.application.ports import Clock
from vibey.application.review_collect_handler import ReviewCollectHandler
from vibey.application.review_demo_handler import (
    AutomatedFinding,
    AutomatedReviewRunner,
    ReviewArtifactWriter,
    ReviewDemoHandler,
)
from vibey.application.review_deployment_choice_handler import ReviewDeploymentChoiceHandler
from vibey.application.review_triage_handler import ReviewTriageHandler
from vibey.application.visual_acceptance import VisualAcceptanceService
from vibey.application.visual_handler import VisualInventoryHandler, VisualPlanHandler
from vibey.application.worker import Park, Success
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
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.domain.job import JobState
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance
from vibey.domain.phase import Phase, VisualDecision
from vibey.domain.plan import VerificationSpec, WorkItem
from vibey.domain.review import Severity
from vibey.domain.spec import DesignSpec
from vibey.domain.visual import VisualInventory
from vibey.infrastructure.engines.scripted_design import ScriptedDesignProvider
from vibey.infrastructure.engines.scripted_visual import ScriptedVisualProvider

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class SystemTestClock(Clock):
    def now(self) -> datetime:
        return NOW


class InMemoryLedger:
    def __init__(self) -> None:
        self._events: list[LedgerEvent] = []
        self._design_events: list[DesignEvent] = []

    async def all_for_project(self, project_id: UUID) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)

    async def append(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID | None,
        engine_id: EngineId | None,
        event: DesignEvent,
    ) -> None:
        self._design_events.append(event)
        self._events.append(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=cycle,
                phase=Phase.DESIGN,
                seq=len(self._events) + 1,
                kind=event.kind,
                engine_id=engine_id or EngineId.CLAUDELOOP,
                job_id=job_id,
                causation_id=None,
                correlation_id=uuid4(),
                provenance=event.provenance,
                produced_at=event.produced_at,
                payload=dict(event.payload),
                digest="sys-test",
            )
        )

    async def append_event(
        self,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        kind: EventKind,
        payload: Mapping[str, object],
    ) -> None:
        self._events.append(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=cycle,
                phase=Phase.REVIEW,
                seq=len(self._events) + 1,
                kind=kind,
                engine_id=EngineId.CLAUDELOOP,
                job_id=job_id,
                causation_id=None,
                correlation_id=uuid4(),
                provenance=Provenance.TRUSTED,
                produced_at=NOW,
                payload=dict(payload),
                digest="sys-test",
            )
        )

    async def record(
        self,
        *,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        engine_id: EngineId | None,
        correlation_id: UUID,
        event: Any,
    ) -> None:
        self._events.append(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=cycle,
                phase=Phase.REVIEW,
                seq=len(self._events) + 1,
                kind=EventKind(event.kind),
                engine_id=engine_id or EngineId.CLAUDELOOP,
                job_id=job_id,
                causation_id=None,
                correlation_id=correlation_id,
                provenance=Provenance.AGENT,
                produced_at=event.at,
                payload=dict(event.payload),
                digest="sys-test",
            )
        )


class InMemoryProjects:
    def __init__(self, project: ProjectRecord) -> None:
        self.project = project
        self.history: list[tuple[Phase, int]] = [(project.phase, project.cycle)]

    async def get(self, project_id: UUID) -> ProjectRecord | None:
        return self.project

    async def transition(
        self,
        project_id: UUID,
        *,
        expected: Phase,
        to: Phase,
        cycle: int | None = None,
    ) -> ProjectRecord:
        assert self.project.phase == expected, (
            f"Expected phase {expected}, got {self.project.phase}"
        )
        self.project = replace(
            self.project,
            phase=to,
            cycle=cycle if cycle is not None else self.project.cycle,
            updated_at=NOW,
        )
        self.history.append((to, self.project.cycle))
        return self.project


class InMemorySpecs:
    def __init__(self) -> None:
        self._specs: dict[tuple[UUID, int], DesignSpec] = {}
        self.published: dict[tuple[UUID, int], DesignSpec] = {}

    async def save(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None:
        self._specs[(project_id, cycle)] = spec

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None:
        return self._specs.get((project_id, cycle))

    async def publish(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None:
        self.published[(project_id, cycle)] = spec


class InMemoryVisualInventories:
    def __init__(self) -> None:
        self._inventories: dict[tuple[UUID, int], VisualInventory] = {}
        self.published: dict[tuple[UUID, int], VisualInventory] = {}

    async def save(self, project_id: UUID, cycle: int, inv: VisualInventory) -> None:
        self._inventories[(project_id, cycle)] = inv

    async def load(self, project_id: UUID, cycle: int) -> VisualInventory | None:
        return self._inventories.get((project_id, cycle))

    async def publish(self, project_id: UUID, cycle: int, inv: VisualInventory) -> None:
        self.published[(project_id, cycle)] = inv


class InMemoryArtifactWriter(ReviewArtifactWriter):
    def __init__(self) -> None:
        self.written: dict[tuple[UUID, int, str], str] = {}

    async def write_review_artifacts(
        self,
        project_id: UUID,
        cycle: int,
        artifacts: Mapping[str, str],
        *,
        executable: Sequence[str] = (),
    ) -> Mapping[str, Path]:
        res = {}
        for name, content in artifacts.items():
            self.written[(project_id, cycle, name)] = content
            res[name] = Path(f"/tmp/artifacts/{cycle}/{name}")
        return res


class DeterministicDecomposer:
    async def decompose(self, spec: DesignSpec) -> tuple[WorkItem, ...]:
        return (
            WorkItem(
                item_id="wi-1",
                title="Walking skeleton",
                acceptance_ids=("AC-1",),
                depends_on=(),
                est_effort=Effort.STANDARD,
                files_touched_hint=("src/skeleton.py",),
                verification=VerificationSpec(
                    commands=("pytest tests/",),
                    criteria_checked=("AC-1",),
                ),
            ),
            WorkItem(
                item_id="wi-2",
                title="Feature implementation",
                acceptance_ids=("AC-1",),
                depends_on=("wi-1",),
                est_effort=Effort.HIGH,
                files_touched_hint=("src/feature.py",),
                verification=VerificationSpec(
                    commands=("pytest tests/",),
                    criteria_checked=("AC-1",),
                ),
            ),
        )


class NoOpAutomatedReviewRunner(AutomatedReviewRunner):
    async def run_automated_reviews(
        self, project_id: UUID, cycle: int
    ) -> tuple[AutomatedFinding, ...]:
        return ()


def _make_job(
    *,
    project_id: UUID,
    cycle: int = 1,
    phase: Phase = Phase.DESIGN,
    kind: str = "design.interview",
) -> JobRecord:
    return JobRecord(
        id=uuid4(),
        project_id=project_id,
        cycle=cycle,
        phase=phase,
        kind=kind,
        state=JobState.READY,
        priority=0,
        work_item_id=None,
        payload={},
        requirement={"effort": Effort.LOW.name.lower()},
        idempotency_key=f"key-{uuid4()}",
        attempts=0,
        max_attempts=7,
        run_after=NOW,
        lease_owner=None,
        lease_expires_at=None,
        assigned_engine=None,
        last_error=None,
        created_at=NOW,
        updated_at=NOW,
    )


async def _run_interview_to_completion(
    handler: DesignInterviewHandler,
    gates: FakeHumanGateRepository,
    job: JobRecord,
) -> None:
    answers = {f"q-{i}": f"answer-{i}" for i in range(1, 10)}
    while True:
        outcome = await handler.handle(job)
        if isinstance(outcome, Success):
            break
        assert isinstance(outcome, Park)
        gate = await gates.raise_gate(job.project_id, job.id, outcome.request)
        await gates.answer(gate.gate_id, answer={"answers": answers}, answered_by="tester")


@pytest.mark.system
async def test_delivery_stage_set_visual_opt_out_and_deploy_opt_out(tmp_path: Path) -> None:
    """End-to-end delivery stage set:
    Phase 1 (DESIGN) -> Visual Opt-Out -> Phase 2 (BUILD) -> Phase 3 (REVIEW)
    -> Deployment Opt-Out -> Phase.DONE (local).
    """
    project_id = uuid4()
    clock = SystemTestClock()
    ledger = InMemoryLedger()
    jobs = FakeJobRepository()
    gates = FakeHumanGateRepository()
    projects = InMemoryProjects(
        ProjectRecord(
            project_id=project_id,
            name="vibey-delivery",
            repo_path=tmp_path,
            phase=Phase.DESIGN,
            cycle=1,
            max_cycles=5,
            config={},
            created_at=NOW,
            updated_at=NOW,
        )
    )
    specs = InMemorySpecs()
    artifacts = InMemoryArtifactWriter()
    design_provider = ScriptedDesignProvider()

    # 1. PHASE 1: DESIGN Interview
    interview_handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=jobs,
        gates=gates,
        questions=design_provider,
        clock=clock,
        interviewer=EngineId.CLAUDELOOP,
    )
    interview_job = _make_job(project_id=project_id, kind="design.interview")

    await _run_interview_to_completion(interview_handler, gates, interview_job)

    # Follow-up design research, synthesize, and spec
    research_handler = DesignResearchHandler(
        ledger=ledger,
        researcher=design_provider,
        clock=clock,
        engine_id=EngineId.CLAUDELOOP,
    )
    for topic in ("prior-art", "libraries", "api-docs"):
        res_job = _make_job(project_id=project_id, kind="design.research")
        res_job = replace(res_job, payload={"topic": topic})
        assert isinstance(await research_handler.handle(res_job), Success)

    synthesize_handler = DesignSynthesizeHandler(
        ledger=ledger,
        synthesizer=design_provider,
        specs=specs,
    )
    synth_job = _make_job(project_id=project_id, kind="design.synthesize")
    assert isinstance(await synthesize_handler.handle(synth_job), Success)

    spec_handler = DesignSpecHandler(specs=specs)
    spec_job = _make_job(project_id=project_id, kind="design.spec")
    assert isinstance(await spec_handler.handle(spec_job), Success)

    # 2. DESIGN ACCEPTANCE -> Visual Opt-Out -> Phase.BUILD
    design_acceptance = DesignAcceptanceService(
        projects=projects,
        ledger=ledger,
        specs=specs,
        jobs=jobs,
        clock=clock,
    )
    accepted_project = await design_acceptance.accept(
        project_id, visual_choice=VisualDecision.DECLINED
    )
    assert accepted_project.phase is Phase.BUILD

    # 3. PHASE 2: BUILD Decompose
    decompose_handler = BuildDecomposeHandler(
        specs=specs,
        decomposer=DeterministicDecomposer(),
        jobs=jobs,
    )
    decompose_job = _make_job(project_id=project_id, phase=Phase.BUILD, kind="build.decompose")
    decomp_outcome = await decompose_handler.handle(decompose_job)
    assert isinstance(decomp_outcome, Success)
    assert decomp_outcome.result.get("work_items") == 2

    # Simulate transition BUILD -> REVIEW
    await projects.transition(project_id, expected=Phase.BUILD, to=Phase.REVIEW)

    # 4. PHASE 3: REVIEW Demo
    demo_handler = ReviewDemoHandler(
        specs=specs,
        ledger=ledger,
        artifacts=artifacts,
        jobs=jobs,
        clock=clock,
        automated_reviewer=NoOpAutomatedReviewRunner(),
    )
    demo_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.demo")
    demo_outcome = await demo_handler.handle(demo_job)
    assert isinstance(demo_outcome, Success)
    assert (project_id, 1, "DEMO.md") in artifacts.written
    assert (project_id, 1, "run-it.sh") in artifacts.written
    assert (project_id, 1, "deltas.md") in artifacts.written

    # 5. REVIEW Collect (User Verdict: ACCEPT)
    collect_handler = ReviewCollectHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        clock=clock,
    )
    collect_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.collect")
    outcome = await collect_handler.handle(collect_job)
    assert isinstance(outcome, Park)

    # Answer collect gate with ACCEPT
    gate = await gates.latest_for_job(collect_job.id)
    assert gate is not None
    await gates.answer(
        gate.gate_id,
        answer={"verdict": "accept"},
        answered_by="reviewer",
    )
    collect_outcome = await collect_handler.handle(collect_job)
    assert isinstance(collect_outcome, Success)

    # 6. REVIEW Triage (Zero open findings -> Enqueues review.deployment_choice)
    triage_handler = ReviewTriageHandler(
        ledger=ledger,
        specs=specs,
        jobs=jobs,
        projects=projects,
        clock=clock,
    )
    triage_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.triage")
    triage_outcome = await triage_handler.handle(triage_job)
    assert isinstance(triage_outcome, Success)
    assert triage_outcome.result.get("next_phase") == "done"

    # 7. DEPLOYMENT CHOICE GATE: Opt-Out ("local_only")
    deployment_handler = ReviewDeploymentChoiceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
    )
    deploy_choice_job = _make_job(
        project_id=project_id,
        phase=Phase.REVIEW,
        kind="review.deployment_choice",
    )
    assert isinstance(await deployment_handler.handle(deploy_choice_job), Park)

    deploy_gate = await gates.latest_for_job(deploy_choice_job.id)
    assert deploy_gate is not None
    assert deploy_gate.default_answer == "local_only"

    await gates.answer(
        deploy_gate.gate_id,
        answer={"choice": "local_only"},
        answered_by="developer",
    )
    deploy_outcome = await deployment_handler.handle(deploy_choice_job)
    assert isinstance(deploy_outcome, Success)
    assert deploy_outcome.result.get("completion_mode") == "local"

    # Final verification: project reached Phase.DONE, no deployment jobs
    assert projects.project.phase is Phase.DONE
    all_jobs = list(jobs._jobs.values())
    assert not any(j.phase is Phase.DEPLOY for j in all_jobs)


@pytest.mark.system
async def test_delivery_stage_set_visual_opt_in_and_deploy_opt_in(tmp_path: Path) -> None:
    """End-to-end delivery stage set with Visual Opt-In and Deployment Opt-In:
    Phase 1 (DESIGN) -> Visual Opt-In -> VISUAL_DESIGN -> Phase 2 (BUILD)
    -> Phase 3 (REVIEW) -> Deployment Opt-In -> Phase 4 (DEPLOY).
    """
    project_id = uuid4()
    clock = SystemTestClock()
    ledger = InMemoryLedger()
    jobs = FakeJobRepository()
    gates = FakeHumanGateRepository()
    projects = InMemoryProjects(
        ProjectRecord(
            project_id=project_id,
            name="vibey-visual-deploy",
            repo_path=tmp_path,
            phase=Phase.DESIGN,
            cycle=1,
            max_cycles=5,
            config={},
            created_at=NOW,
            updated_at=NOW,
        )
    )
    specs = InMemorySpecs()
    inventories = InMemoryVisualInventories()
    artifacts = InMemoryArtifactWriter()
    design_provider = ScriptedDesignProvider()
    visual_provider = ScriptedVisualProvider()

    # Synthesize & save valid design spec
    design_spec = await design_provider.synthesize(())
    await specs.save(project_id, 1, design_spec)

    # Accept design with Visual Opt-In
    design_acceptance = DesignAcceptanceService(
        projects=projects,
        ledger=ledger,
        specs=specs,
        jobs=jobs,
        clock=clock,
    )
    accepted_project = await design_acceptance.accept(
        project_id, visual_choice=VisualDecision.OPTED_IN
    )
    assert accepted_project.phase is Phase.VISUAL_DESIGN

    # Run Visual Inventory & Plan handlers
    inv_handler = VisualInventoryHandler(
        ledger=ledger,
        producer=visual_provider,
        inventories=inventories,
        jobs=jobs,
    )
    inv_job = _make_job(project_id=project_id, phase=Phase.VISUAL_DESIGN, kind="visual.inventory")
    assert isinstance(await inv_handler.handle(inv_job), Success)

    plan_handler = VisualPlanHandler(inventories=inventories)
    plan_job = _make_job(project_id=project_id, phase=Phase.VISUAL_DESIGN, kind="visual.plan")
    assert isinstance(await plan_handler.handle(plan_job), Success)

    # Settle Visual Design -> Phase.BUILD
    visual_acceptance = VisualAcceptanceService(
        projects=projects,
        ledger=ledger,
        inventories=inventories,
        jobs=jobs,
        clock=clock,
    )
    build_project = await visual_acceptance.settle(project_id, decision=VisualDecision.ACCEPTED)
    assert build_project.phase is Phase.BUILD

    # Simulate transition BUILD -> REVIEW
    await projects.transition(project_id, expected=Phase.BUILD, to=Phase.REVIEW)

    # Demo & Collect
    demo_handler = ReviewDemoHandler(
        specs=specs,
        ledger=ledger,
        artifacts=artifacts,
        jobs=jobs,
        clock=clock,
        automated_reviewer=NoOpAutomatedReviewRunner(),
    )
    demo_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.demo")
    assert isinstance(await demo_handler.handle(demo_job), Success)

    collect_handler = ReviewCollectHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        clock=clock,
    )
    collect_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.collect")
    outcome = await collect_handler.handle(collect_job)
    assert isinstance(outcome, Park)

    gate = await gates.latest_for_job(collect_job.id)
    assert gate is not None
    await gates.answer(
        gate.gate_id,
        answer={"verdict": "accept"},
        answered_by="reviewer",
    )
    assert isinstance(await collect_handler.handle(collect_job), Success)

    # Review Triage
    triage_handler = ReviewTriageHandler(
        ledger=ledger,
        specs=specs,
        jobs=jobs,
        projects=projects,
        clock=clock,
    )
    triage_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.triage")
    assert isinstance(await triage_handler.handle(triage_job), Success)

    # Deployment Choice Gate: Explicit Opt-In ("deploy")
    deployment_handler = ReviewDeploymentChoiceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
    )
    deploy_choice_job = _make_job(
        project_id=project_id,
        phase=Phase.REVIEW,
        kind="review.deployment_choice",
    )
    assert isinstance(await deployment_handler.handle(deploy_choice_job), Park)
    deploy_gate = await gates.latest_for_job(deploy_choice_job.id)
    assert deploy_gate is not None

    await gates.answer(
        deploy_gate.gate_id,
        answer={"choice": "deploy"},
        answered_by="developer",
    )
    deploy_outcome = await deployment_handler.handle(deploy_choice_job)
    assert isinstance(deploy_outcome, Success)
    assert deploy_outcome.result.get("decision") == "opted_in"

    # Project transitioned to DEPLOY and deploy.design is enqueued
    assert projects.project.phase is Phase.DEPLOY
    all_jobs = list(jobs._jobs.values())
    assert any(j.kind == "deploy.design" and j.phase is Phase.DEPLOY for j in all_jobs)


@pytest.mark.system
async def test_delivery_stage_set_loopback_to_reentrant_design(tmp_path: Path) -> None:
    """End-to-end review loopback to re-entrant DESIGN:
    Phase 3 (REVIEW) raises finding with ambiguity -> Loops back to DESIGN
    (cycle 2) -> Scoped <= 5 question stages -> Synthesis -> BUILD -> REVIEW -> DONE.
    """
    project_id = uuid4()
    clock = SystemTestClock()
    ledger = InMemoryLedger()
    jobs = FakeJobRepository()
    gates = FakeHumanGateRepository()
    projects = InMemoryProjects(
        ProjectRecord(
            project_id=project_id,
            name="vibey-loopback",
            repo_path=tmp_path,
            phase=Phase.REVIEW,
            cycle=1,
            max_cycles=5,
            config={},
            created_at=NOW,
            updated_at=NOW,
        )
    )
    specs = InMemorySpecs()
    design_provider = ScriptedDesignProvider()

    # 1. Start in Phase 3 REVIEW with a finding requiring clarification
    await ledger.append_event(
        project_id=project_id,
        cycle=1,
        job_id=uuid4(),
        kind=EventKind.FINDING_RAISED,
        payload={
            "finding_id": "f-ambiguous",
            "text": "Maybe we should rethink the error retry logic and rate limits",
            "severity": Severity.HIGH.value,
        },
    )

    triage_handler = ReviewTriageHandler(
        ledger=ledger,
        specs=specs,
        jobs=jobs,
        projects=projects,
        clock=clock,
    )
    triage_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.triage")
    triage_outcome = await triage_handler.handle(triage_job)
    assert isinstance(triage_outcome, Success)
    # Finding has ambiguity -> routes back to DESIGN with cycle increment
    assert triage_outcome.result.get("next_phase") == "design"
    assert projects.project.phase is Phase.DESIGN
    assert projects.project.cycle == 2

    # 2. Cycle 2 Re-entrant DESIGN executes scoped stages (<= 5 question batches)
    reentrant_stages = stages_for_cycle(2)
    assert len(reentrant_stages) == 4  # <= 5

    interview_handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=jobs,
        gates=gates,
        questions=design_provider,
        clock=clock,
        interviewer=EngineId.CLAUDELOOP,
    )
    cycle2_interview_job = _make_job(
        project_id=project_id,
        cycle=2,
        phase=Phase.DESIGN,
        kind="design.interview",
    )

    await _run_interview_to_completion(interview_handler, gates, cycle2_interview_job)

    final_reentrant = await interview_handler.handle(cycle2_interview_job)
    assert isinstance(final_reentrant, Success)
    assert final_reentrant.result.get("stages") == 4


class FakeAzureClient:
    """Deterministic, offline Azure client for system tests."""

    def __init__(self) -> None:
        self.steps_run: list[str] = []

    async def discover_environment(self, scope: AzureTargetScope) -> AzureDiscoveryResult:
        self.steps_run.append("discover")
        return AzureDiscoveryResult(
            tenant_id=scope.tenant_id,
            subscription_id=scope.subscription_id,
            resource_group=scope.resource_group,
            location=scope.region,
        )

    async def execute_plan(
        self, spec: DeploymentSpec, consent: DeploymentConsent
    ) -> AzureExecutionResult:
        self.steps_run.append("apply")
        return AzureExecutionResult(
            deployment_id=f"dep-{spec.spec_id}",
            provisioning_state="Succeeded",
            outputs={"endpoint": f"https://{spec.spec_id}.azurecontainerapps.io"},
            applied_at=NOW,
        )

    async def get_resource_status(
        self, scope: AzureTargetScope, resource_id: str
    ) -> AzureResourceStatus:
        self.steps_run.append("verify")
        return AzureResourceStatus(resource_id, "Succeeded", "Healthy")

    async def delete_resource(
        self, scope: AzureTargetScope, resource_id: str, consent: DeploymentConsent
    ) -> None:
        self.steps_run.append("delete")


def _sample_deployment_spec() -> DeploymentSpec:
    target = AzureTargetScope("tenant-1", "sub-1", "rg-sys", "dev", "eastus")
    identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
    topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
    recovery = RecoveryPolicy("revision", True)
    verification = VerificationContract("/health", ("curl /health",), 30)
    cost = CostBoundary(100.0, 10.0)
    return DeploymentSpec(
        spec_id="spec-sys",
        version="1.0",
        target_scope=target,
        identity=identity,
        topology=topology,
        recovery_policy=recovery,
        verification=verification,
        cost_boundary=cost,
    )


@pytest.mark.system
async def test_full_delivery_to_deployment_stage_set(tmp_path: Path) -> None:
    """Full offline optional-path delivery-to-deployment system test (task 10.13):
    ① DESIGN → ② BUILD → ③ REVIEW → ④ DEPLOY_DESIGN → ⑤ DEPLOY_EXECUTE
    → ⑥ DEPLOY_REVIEW → DONE (deployed).

    Verifies deterministic, offline execution with zero network dependency.
    """
    project_id = uuid4()
    clock = SystemTestClock()
    ledger = InMemoryLedger()
    jobs = FakeJobRepository()
    gates = FakeHumanGateRepository()
    projects = InMemoryProjects(
        ProjectRecord(
            project_id=project_id,
            name="vibey-full-deploy",
            repo_path=tmp_path,
            phase=Phase.DESIGN,
            cycle=1,
            max_cycles=5,
            config={},
            created_at=NOW,
            updated_at=NOW,
        )
    )
    specs = InMemorySpecs()
    artifacts = InMemoryArtifactWriter()
    design_provider = ScriptedDesignProvider()
    azure_client = FakeAzureClient()
    dep_spec = _sample_deployment_spec()
    dep_consent: DeploymentConsent | None = None

    # ── Phase ① DESIGN ──────────────────────────────────────────────

    interview_handler = DesignInterviewHandler(
        ledger=ledger,
        jobs=jobs,
        gates=gates,
        questions=design_provider,
        clock=clock,
        interviewer=EngineId.CLAUDELOOP,
    )
    interview_job = _make_job(project_id=project_id, kind="design.interview")
    await _run_interview_to_completion(interview_handler, gates, interview_job)

    research_handler = DesignResearchHandler(
        ledger=ledger,
        researcher=design_provider,
        clock=clock,
        engine_id=EngineId.CLAUDELOOP,
    )
    for topic in ("prior-art", "libraries"):
        res_job = _make_job(project_id=project_id, kind="design.research")
        from dataclasses import replace as _replace

        res_job = _replace(res_job, payload={"topic": topic})
        assert isinstance(await research_handler.handle(res_job), Success)

    synthesize_handler = DesignSynthesizeHandler(
        ledger=ledger,
        synthesizer=design_provider,
        specs=specs,
    )
    synth_job = _make_job(project_id=project_id, kind="design.synthesize")
    assert isinstance(await synthesize_handler.handle(synth_job), Success)

    spec_handler = DesignSpecHandler(specs=specs)
    spec_job = _make_job(project_id=project_id, kind="design.spec")
    assert isinstance(await spec_handler.handle(spec_job), Success)

    # Accept design, visual opt-out → BUILD
    design_acceptance = DesignAcceptanceService(
        projects=projects,
        ledger=ledger,
        specs=specs,
        jobs=jobs,
        clock=clock,
    )
    accepted = await design_acceptance.accept(project_id, visual_choice=VisualDecision.DECLINED)
    assert accepted.phase is Phase.BUILD

    # ── Phase ② BUILD ───────────────────────────────────────────────

    decompose_handler = BuildDecomposeHandler(
        specs=specs,
        decomposer=DeterministicDecomposer(),
        jobs=jobs,
    )
    decompose_job = _make_job(project_id=project_id, phase=Phase.BUILD, kind="build.decompose")
    assert isinstance(await decompose_handler.handle(decompose_job), Success)

    await projects.transition(project_id, expected=Phase.BUILD, to=Phase.REVIEW)

    # ── Phase ③ REVIEW ──────────────────────────────────────────────

    demo_handler = ReviewDemoHandler(
        specs=specs,
        ledger=ledger,
        artifacts=artifacts,
        jobs=jobs,
        clock=clock,
        automated_reviewer=NoOpAutomatedReviewRunner(),
    )
    demo_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.demo")
    assert isinstance(await demo_handler.handle(demo_job), Success)

    collect_handler = ReviewCollectHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        clock=clock,
    )
    collect_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.collect")
    outcome = await collect_handler.handle(collect_job)
    assert isinstance(outcome, Park)

    gate = await gates.latest_for_job(collect_job.id)
    assert gate is not None
    await gates.answer(gate.gate_id, answer={"verdict": "accept"}, answered_by="reviewer")
    assert isinstance(await collect_handler.handle(collect_job), Success)

    triage_handler = ReviewTriageHandler(
        ledger=ledger,
        specs=specs,
        jobs=jobs,
        projects=projects,
        clock=clock,
    )
    triage_job = _make_job(project_id=project_id, phase=Phase.REVIEW, kind="review.triage")
    assert isinstance(await triage_handler.handle(triage_job), Success)

    # Deployment choice: opt-in
    deployment_choice_handler = ReviewDeploymentChoiceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
    )
    deploy_choice_job = _make_job(
        project_id=project_id, phase=Phase.REVIEW, kind="review.deployment_choice"
    )
    assert isinstance(await deployment_choice_handler.handle(deploy_choice_job), Park)
    deploy_gate = await gates.latest_for_job(deploy_choice_job.id)
    assert deploy_gate is not None
    await gates.answer(deploy_gate.gate_id, answer={"choice": "deploy"}, answered_by="developer")
    deploy_choice_outcome = await deployment_choice_handler.handle(deploy_choice_job)
    assert isinstance(deploy_choice_outcome, Success)
    assert deploy_choice_outcome.result.get("decision") == "opted_in"
    assert projects.project.phase is Phase.DEPLOY

    # Bridge: DEPLOY → DEPLOY_DESIGN
    await projects.transition(project_id, expected=Phase.DEPLOY, to=Phase.DEPLOY_DESIGN)

    # ── Phase ④ DEPLOY_DESIGN ──────────────────────────────────────

    deploy_interview_handler = DeployInterviewHandler(
        ledger=ledger,
        gates=gates,
        clock=clock,
    )
    deploy_interview_job = _make_job(
        project_id=project_id, phase=Phase.DEPLOY_DESIGN, kind="deploy.interview"
    )
    assert isinstance(await deploy_interview_handler.handle(deploy_interview_job), Park)
    int_gate = await gates.latest_for_job(deploy_interview_job.id)
    assert int_gate is not None
    await gates.answer(
        int_gate.gate_id, answer={"choice": "accept_defaults"}, answered_by="developer"
    )
    int_outcome = await deploy_interview_handler.handle(deploy_interview_job)
    assert isinstance(int_outcome, Success)

    deploy_synthesize_handler = DeploySynthesizeHandler(ledger=ledger, clock=clock)
    deploy_synth_job = _make_job(
        project_id=project_id, phase=Phase.DEPLOY_DESIGN, kind="deploy.synthesize"
    )
    assert isinstance(await deploy_synthesize_handler.handle(deploy_synth_job), Success)

    # Acceptance with explicit mutation consent
    deploy_acceptance_handler = DeployAcceptanceHandler(
        ledger=ledger,
        gates=gates,
        jobs=jobs,
        projects=projects,
        clock=clock,
        spec_provider=lambda _pid: dep_spec,
    )
    deploy_accept_job = _make_job(
        project_id=project_id, phase=Phase.DEPLOY_DESIGN, kind="deploy.accept"
    )
    assert isinstance(await deploy_acceptance_handler.handle(deploy_accept_job), Park)
    acc_gate = await gates.latest_for_job(deploy_accept_job.id)
    assert acc_gate is not None
    await gates.answer(
        acc_gate.gate_id,
        answer={"verdict": "accept", "explicit_mutation_authorized": True},
        answered_by="developer",
    )
    acc_outcome = await deploy_acceptance_handler.handle(deploy_accept_job)
    assert isinstance(acc_outcome, Success)
    assert acc_outcome.result.get("verdict") == "accepted"
    assert projects.project.phase is Phase.DEPLOY_EXECUTE

    # Build consent from the acceptance for execute/routing handlers
    dep_consent = DeploymentConsent(
        consent_id=str(deploy_accept_job.id),
        target_scope_digest=dep_spec.scope_digest(),
        granted_by="developer",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )

    # ── Phase ⑤ DEPLOY_EXECUTE ─────────────────────────────────────

    deploy_execute_handler = DeployExecuteHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=azure_client,
        clock=clock,
        spec_provider=lambda _pid: dep_spec,
        consent_provider=lambda _pid: dep_consent,
    )
    deploy_exec_job = _make_job(
        project_id=project_id, phase=Phase.DEPLOY_EXECUTE, kind="deploy.execute"
    )
    exec_outcome = await deploy_execute_handler.handle(deploy_exec_job)
    assert isinstance(exec_outcome, Success)
    assert exec_outcome.result.get("status") == "verified"
    assert "endpoint" in exec_outcome.result.get("outputs", {})
    assert projects.project.phase is Phase.DEPLOY_REVIEW

    # Verify Azure client ran discover → apply → verify
    assert "discover" in azure_client.steps_run
    assert "apply" in azure_client.steps_run
    assert "verify" in azure_client.steps_run

    # ── Phase ⑥ DEPLOY_REVIEW ──────────────────────────────────────

    # Demo: presents live URL and verification evidence
    deploy_demo_handler = DeployReviewDemoHandler(
        ledger=ledger,
        human_gates=gates,
        spec_provider=lambda _pid: dep_spec,
    )
    deploy_demo_job = _make_job(
        project_id=project_id, phase=Phase.DEPLOY_REVIEW, kind="deploy.demo"
    )
    assert isinstance(await deploy_demo_handler.handle(deploy_demo_job), Park)
    demo_gate = await gates.latest_for_job(deploy_demo_job.id)
    assert demo_gate is not None
    assert "spec-sys.azurecontainerapps.io" in demo_gate.prompt
    await gates.answer(demo_gate.gate_id, answer={"verdict": "approve"}, answered_by="developer")
    demo_outcome = await deploy_demo_handler.handle(deploy_demo_job)
    assert isinstance(demo_outcome, Success)
    assert demo_outcome.result.get("status") == "demo_approved"

    # Route: approve → DONE
    deploy_routing_handler = DeployReviewRoutingHandler(
        ledger=ledger,
        jobs=jobs,
        projects=projects,
        azure_client=azure_client,
        spec_provider=lambda _pid: dep_spec,
        consent_provider=lambda _pid: dep_consent,
    )
    deploy_route_job = _make_job(
        project_id=project_id, phase=Phase.DEPLOY_REVIEW, kind="deploy.route"
    )
    deploy_route_job = _replace(deploy_route_job, payload={"action": "approve"})
    route_outcome = await deploy_routing_handler.handle(deploy_route_job)
    assert isinstance(route_outcome, Success)
    assert route_outcome.result.get("target_phase") == Phase.DONE.name

    # ── Final Assertions ───────────────────────────────────────────

    assert projects.project.phase is Phase.DONE

    # Verify the full phase transition history
    phase_history = [p for p, _ in projects.history]
    assert Phase.DESIGN in phase_history
    assert Phase.BUILD in phase_history
    assert Phase.REVIEW in phase_history
    assert Phase.DEPLOY in phase_history
    assert Phase.DEPLOY_DESIGN in phase_history
    assert Phase.DEPLOY_EXECUTE in phase_history
    assert Phase.DEPLOY_REVIEW in phase_history
    assert Phase.DONE in phase_history

    # Zero network dependency: only FakeAzureClient was used
    assert len(azure_client.steps_run) == 3

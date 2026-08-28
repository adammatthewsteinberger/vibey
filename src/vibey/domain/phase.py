# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The phase machine: legal transitions, guards, and the review loop-back
routing decision from ADR-0010 and ADR-0013/ADR-0014."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from vibey.domain.errors import InvalidPhaseError
from vibey.domain.review import Ambiguity, FindingRef, UserVerdict


class Phase(StrEnum):
    INTAKE = "intake"
    DESIGN = "design"
    VISUAL_DESIGN = "visual_design"  # optional, unnumbered interstitial
    BUILD = "build"
    REVIEW = "review"
    DEPLOY_DESIGN = "deploy_design"  # Phase ④
    DEPLOY_EXECUTE = "deploy_execute"  # Phase ⑤
    DEPLOY_REVIEW = "deploy_review"  # Phase ⑥
    DEPLOY = "deploy"  # legacy single-phase bridge
    DONE = "done"
    ABANDONED = "abandoned"


class CompletionMode(StrEnum):
    LOCAL = "local"
    DEPLOYED = "deployed"


class VisualDecision(StrEnum):
    OPTED_IN = "opted_in"
    DECLINED = "declined"
    ACCEPTED = "accepted"
    WAIVED = "waived"


class DeploymentDecision(StrEnum):
    OPTED_IN = "opted_in"
    DECLINED = "declined"


TERMINAL: frozenset[Phase] = frozenset({Phase.DONE, Phase.ABANDONED})
INTERACTIVE: frozenset[Phase] = frozenset(
    {
        Phase.DESIGN,
        Phase.VISUAL_DESIGN,
        Phase.REVIEW,
        Phase.DEPLOY_DESIGN,
        Phase.DEPLOY_REVIEW,
    }
)

# The legal edges of the phase machine, independent of guard evaluation.
_EDGES: dict[Phase, frozenset[Phase]] = {
    Phase.INTAKE: frozenset({Phase.DESIGN}),
    Phase.DESIGN: frozenset({Phase.BUILD, Phase.VISUAL_DESIGN, Phase.ABANDONED}),
    Phase.VISUAL_DESIGN: frozenset({Phase.BUILD, Phase.ABANDONED}),
    Phase.BUILD: frozenset({Phase.REVIEW, Phase.DESIGN, Phase.ABANDONED}),
    Phase.REVIEW: frozenset(
        {
            Phase.DONE,
            Phase.DESIGN,
            Phase.BUILD,
            Phase.DEPLOY_DESIGN,
            Phase.DEPLOY,
            Phase.ABANDONED,
        }
    ),
    Phase.DEPLOY: frozenset({Phase.DONE, Phase.REVIEW, Phase.DEPLOY_DESIGN, Phase.ABANDONED}),
    Phase.DEPLOY_DESIGN: frozenset({Phase.DEPLOY_EXECUTE, Phase.DEPLOY_DESIGN, Phase.ABANDONED}),
    Phase.DEPLOY_EXECUTE: frozenset({Phase.DEPLOY_REVIEW, Phase.DEPLOY_EXECUTE, Phase.ABANDONED}),
    Phase.DEPLOY_REVIEW: frozenset(
        {
            Phase.DONE,
            Phase.DEPLOY_DESIGN,
            Phase.DEPLOY_EXECUTE,
            Phase.DESIGN,
            Phase.BUILD,
            Phase.REVIEW,
            Phase.ABANDONED,
        }
    ),
    Phase.DONE: frozenset({Phase.DEPLOY, Phase.DEPLOY_DESIGN}),
    Phase.ABANDONED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class PhaseState:
    phase: Phase
    cycle: int
    max_cycles: int
    entered_at: datetime

    def __post_init__(self) -> None:
        if self.cycle < 1:
            raise InvalidPhaseError("cycle must be >= 1")
        if self.max_cycles < 1:
            raise InvalidPhaseError("max_cycles must be >= 1")


@dataclass(frozen=True, slots=True)
class TransitionEvidence:
    """Everything a guard needs. Assembled by application/, evaluated here."""

    acceptance_criteria: int = 0
    open_blocking_questions: int = 0
    unmapped_criteria: tuple[str, ...] = ()
    work_items_total: int = 0
    work_items_settled: int = 0
    integration_green: bool = False
    criteria_with_passing_tests: int = 0
    build_savepoint_exists: bool = False
    open_findings: tuple[FindingRef, ...] = ()
    user_verdict: UserVerdict | None = None
    budget_exhausted: bool = False
    blocked_on_ambiguity: int = 0
    visual_decision: VisualDecision | None = None
    visual_inventory_complete: bool = False
    deployment_decision: DeploymentDecision | None = None
    completion_mode: CompletionMode | None = None
    deployment_spec_accepted: bool = False
    deployment_consent_recorded: bool = False
    deployment_verified: bool = False
    deployment_requires_user_input: bool = False
    deployment_demo_accepted: bool = False
    deployment_attempts: int = 0
    max_deployment_attempts: int = 5


@dataclass(frozen=True, slots=True)
class TransitionRequest:
    to: Phase
    reason: str
    evidence: TransitionEvidence


Allowed = Literal["allowed"]
ALLOWED: Allowed = "allowed"


@dataclass(frozen=True, slots=True)
class Denied:
    violations: tuple[str, ...]


TransitionOutcome = Allowed | Denied


def _guard_design_common(evidence: TransitionEvidence) -> list[str]:
    violations = []
    if evidence.acceptance_criteria < 1:
        violations.append("at least one acceptance criterion is required")
    if evidence.open_blocking_questions > 0:
        violations.append(f"{evidence.open_blocking_questions} blocking question(s) still open")
    if evidence.unmapped_criteria:
        violations.append(
            f"{len(evidence.unmapped_criteria)} acceptance criterion/criteria unmapped"
        )
    if evidence.user_verdict is not UserVerdict.ACCEPT:
        violations.append("design has not been accepted by the user")
    return violations


def _guard_design_to_build(evidence: TransitionEvidence) -> tuple[str, ...]:
    violations = _guard_design_common(evidence)
    if evidence.visual_decision is not VisualDecision.DECLINED:
        violations.append(
            "design -> build requires an explicit visual-design decline "
            "(opt-in must route through visual_design first)"
        )
    return tuple(violations)


def _guard_design_to_visual_design(evidence: TransitionEvidence) -> tuple[str, ...]:
    violations = _guard_design_common(evidence)
    if evidence.visual_decision is not VisualDecision.OPTED_IN:
        violations.append("design -> visual_design requires an explicit visual-design opt-in")
    return tuple(violations)


def _guard_visual_design_to_build(evidence: TransitionEvidence) -> tuple[str, ...]:
    violations = []
    if evidence.visual_decision not in (VisualDecision.ACCEPTED, VisualDecision.WAIVED):
        violations.append(
            "visual_design -> build requires the visual plan to be accepted or explicitly waived"
        )
    if not evidence.visual_inventory_complete:
        violations.append(
            "visual_design -> build requires a complete screen/state inventory "
            "(build cannot consume an incomplete or unreviewed visual plan)"
        )
    return tuple(violations)


def _guard_build_to_review(evidence: TransitionEvidence) -> tuple[str, ...]:
    violations = []
    if evidence.work_items_total == 0:
        violations.append("no work items to review")
    elif evidence.work_items_settled < evidence.work_items_total:
        remaining = evidence.work_items_total - evidence.work_items_settled
        violations.append(f"{remaining} work item(s) not yet integrated or waived")
    if not evidence.integration_green:
        violations.append("integration branch is not green")
    if evidence.criteria_with_passing_tests < evidence.acceptance_criteria:
        gap = evidence.acceptance_criteria - evidence.criteria_with_passing_tests
        violations.append(f"{gap} acceptance criterion/criteria without a passing test")
    if not evidence.build_savepoint_exists:
        violations.append("no build savepoint exists at the integration head")
    return tuple(violations)


def _guard_build_to_design(evidence: TransitionEvidence) -> tuple[str, ...]:
    if evidence.blocked_on_ambiguity < 1:
        return ("BUILD -> DESIGN requires at least 1 item blocked on ambiguity",)
    return ()


def _guard_review_to_done(evidence: TransitionEvidence) -> tuple[str, ...]:
    if evidence.open_findings:
        return (f"{len(evidence.open_findings)} finding(s) still open",)
    if evidence.user_verdict is not UserVerdict.ACCEPT:
        return ("user has not accepted the review",)
    return ()


def _guard_done_to_deploy(evidence: TransitionEvidence) -> tuple[str, ...]:
    if evidence.deployment_decision is not DeploymentDecision.OPTED_IN:
        return ("DEPLOY requires explicit deployment opt-in",)
    return ()


def _guard_done_to_deploy_design(evidence: TransitionEvidence) -> tuple[str, ...]:
    if evidence.deployment_decision is not DeploymentDecision.OPTED_IN:
        return ("DEPLOY_DESIGN requires explicit deployment opt-in",)
    return ()


def _guard_review_to_deploy_design(evidence: TransitionEvidence) -> tuple[str, ...]:
    if evidence.deployment_decision is not DeploymentDecision.OPTED_IN:
        return ("DEPLOY_DESIGN requires explicit deployment opt-in",)
    return ()


def _guard_deploy_design_to_deploy_execute(evidence: TransitionEvidence) -> tuple[str, ...]:
    violations = []
    if not evidence.deployment_spec_accepted:
        violations.append("deployment specification has not been accepted")
    if not evidence.deployment_consent_recorded:
        violations.append("deployment consent has not been recorded")
    return tuple(violations)


def _guard_deploy_execute_to_deploy_review(evidence: TransitionEvidence) -> tuple[str, ...]:
    if not (evidence.deployment_verified or evidence.deployment_requires_user_input):
        return (
            "DEPLOY_EXECUTE -> DEPLOY_REVIEW requires verified deployment or "
            "classified user-input needed",
        )
    return ()


def _guard_deploy_review_to_done(evidence: TransitionEvidence) -> tuple[str, ...]:
    if not evidence.deployment_demo_accepted:
        return ("DEPLOY_REVIEW -> DONE requires deployment demo to be accepted",)
    return ()


_GUARDS = {
    (Phase.DESIGN, Phase.BUILD): _guard_design_to_build,
    (Phase.DESIGN, Phase.VISUAL_DESIGN): _guard_design_to_visual_design,
    (Phase.VISUAL_DESIGN, Phase.BUILD): _guard_visual_design_to_build,
    (Phase.BUILD, Phase.REVIEW): _guard_build_to_review,
    (Phase.BUILD, Phase.DESIGN): _guard_build_to_design,
    (Phase.REVIEW, Phase.DONE): _guard_review_to_done,
    (Phase.REVIEW, Phase.DEPLOY_DESIGN): _guard_review_to_deploy_design,
    (Phase.DONE, Phase.DEPLOY): _guard_done_to_deploy,
    (Phase.DONE, Phase.DEPLOY_DESIGN): _guard_done_to_deploy_design,
    (Phase.DEPLOY_DESIGN, Phase.DEPLOY_EXECUTE): _guard_deploy_design_to_deploy_execute,
    (Phase.DEPLOY_EXECUTE, Phase.DEPLOY_REVIEW): _guard_deploy_execute_to_deploy_review,
    (Phase.DEPLOY_REVIEW, Phase.DONE): _guard_deploy_review_to_done,
}


def evaluate_transition(state: PhaseState, request: TransitionRequest) -> TransitionOutcome:
    if request.to not in _EDGES.get(state.phase, frozenset()):
        return Denied((f"{state.phase} -> {request.to} is not a legal edge",))

    if state.cycle > state.max_cycles and request.to is not Phase.ABANDONED:
        return Denied((f"cycle {state.cycle} exceeds max_cycles {state.max_cycles}",))

    guard = _GUARDS.get((state.phase, request.to))
    if guard is not None:
        violations = guard(request.evidence)
        if violations:
            return Denied(violations)

    return ALLOWED


def next_phase_after_design(*, visual_decision: VisualDecision, spec_is_buildable: bool) -> Phase:
    """Choose the optional visual interstitial or the direct BUILD path."""
    if not spec_is_buildable:
        raise InvalidPhaseError("cannot route out of DESIGN with a non-buildable spec")
    if visual_decision is VisualDecision.OPTED_IN:
        return Phase.VISUAL_DESIGN
    return Phase.BUILD


def next_phase_after_review(findings: Sequence[FindingRef], *, strict_loopback: bool) -> Phase:
    """The routing decision from ADR-0010, isolated so it is trivially testable."""
    if not findings:
        return Phase.DONE
    if strict_loopback:
        return Phase.DESIGN
    if any(f.ambiguity is Ambiguity.NEEDS_CLARIFICATION for f in findings):
        return Phase.DESIGN
    return Phase.BUILD


def next_phase_after_deploy_review(
    findings: Sequence[FindingRef] = (),
    *,
    demo_accepted: bool = False,
    target_changed: bool = False,
    retry_unambiguous: bool = False,
    code_defect: bool = False,
) -> Phase:
    """The routing decision from ADR-0013 for Phase ⑥ DEPLOY REVIEW."""
    if demo_accepted or (
        not findings and not target_changed and not retry_unambiguous and not code_defect
    ):
        return Phase.DONE
    if code_defect:
        return Phase.DESIGN
    if target_changed:
        return Phase.DEPLOY_DESIGN
    if retry_unambiguous:
        return Phase.DEPLOY_EXECUTE
    return Phase.DONE

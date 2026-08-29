# Domain Model

> Everything in `src/vibey/domain/`. **Stdlib only** — no I/O, no async, no
> third-party imports, enforced by `import-linter`. Every type here is frozen and
> slotted; every function is pure. This is the layer that carries a 100% coverage
> floor, because it is the layer where being wrong is silent.

---

## 1. Why the domain is this large

A thin domain would push the six-phase machine, the rotation algorithm, and the
no-loss gate into `application/`, where they would be tested against fakes rather
than against their own properties. The three things vibey must get right —
*which engine next*, *did the handoff lose anything*, *is this transition legal* —
are all pure functions of state. They belong here, where Hypothesis can attack
them without a database.

---

## 2. `phase.py`

```python
class Phase(StrEnum):
    INTAKE = "intake"; DESIGN = "design"; VISUAL_DESIGN = "visual_design"
    BUILD = "build"; REVIEW = "review"
    DEPLOY_DESIGN = "deploy_design"      # Phase ④
    DEPLOY_EXECUTE = "deploy_execute"    # Phase ⑤
    DEPLOY_REVIEW = "deploy_review"      # Phase ⑥
    DEPLOY = "deploy"                    # legacy single-phase bridge
    DONE = "done"; ABANDONED = "abandoned"


TERMINAL: frozenset[Phase] = frozenset({Phase.DONE, Phase.ABANDONED})
INTERACTIVE: frozenset[Phase] = frozenset({
    Phase.DESIGN, Phase.VISUAL_DESIGN, Phase.REVIEW,
    Phase.DEPLOY_DESIGN, Phase.DEPLOY_REVIEW,
})


class CompletionMode(StrEnum):
    LOCAL = "local"; DEPLOYED = "deployed"


class VisualDecision(StrEnum):
    OPTED_IN = "opted_in"; DECLINED = "declined"; ACCEPTED = "accepted"
    WAIVED = "waived"


class DeploymentDecision(StrEnum):
    OPTED_IN = "opted_in"; DECLINED = "declined"
```

`Phase.DEPLOY` is a legacy single-phase bridge kept alongside the ④–⑥
deployment stage set (`DEPLOY_DESIGN` / `DEPLOY_EXECUTE` / `DEPLOY_REVIEW`);
both `DONE` and `REVIEW` still have edges into it. The legal edges of the
machine live in a private `_EDGES: dict[Phase, frozenset[Phase]]` table,
checked independently of guard evaluation.

```python
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


def evaluate_transition(state: PhaseState, request: TransitionRequest) -> TransitionOutcome:
    """Checked in order: (1) the edge must exist in `_EDGES`, (2) `cycle` must
    not exceed `max_cycles` unless routing to `ABANDONED`, (3) any per-edge
    guard registered in `_GUARDS` must report no violations."""


def next_phase_after_design(*, visual_decision: VisualDecision, spec_is_buildable: bool) -> Phase:
    """Raises InvalidPhaseError on a non-buildable spec; otherwise VISUAL_DESIGN
    on opt-in, else BUILD directly."""


def next_phase_after_review(findings: Sequence[FindingRef], *, strict_loopback: bool) -> Phase:
    """The routing decision from ADR-0010. No findings -> DONE. strict_loopback
    or any NEEDS_CLARIFICATION finding -> DESIGN. Otherwise -> BUILD."""


def next_phase_after_deploy_review(
    findings: Sequence[FindingRef] = (),
    *,
    demo_accepted: bool = False,
    target_changed: bool = False,
    retry_unambiguous: bool = False,
    code_defect: bool = False,
) -> Phase:
    """The routing decision from ADR-0013 for Phase ⑥. Priority order:
    demo accepted (or nothing outstanding) -> DONE; a code defect -> DESIGN;
    a changed deployment target -> DEPLOY_DESIGN; an unambiguous retry ->
    DEPLOY_EXECUTE; otherwise -> DONE."""
```

Every guard function (`_guard_design_to_build`, `_guard_build_to_review`, …) is
registered in a private `_GUARDS: dict[tuple[Phase, Phase], Callable]` table
keyed by the edge it guards, so `evaluate_transition` never has to know which
guard applies — it just looks the edge up.

### Invariants

- `DONE` and `ABANDONED` have no outgoing edges except `DONE`'s bridge into
  `DEPLOY` / `DEPLOY_DESIGN`.
- No transition is legal when `cycle > max_cycles` except `→ ABANDONED`.
- `DESIGN → BUILD` requires an explicit visual-design **decline**; opting in
  must route through `VISUAL_DESIGN` first.
- `VISUAL_DESIGN → BUILD` requires the visual plan accepted-or-waived *and* a
  complete screen/state inventory.
- `BUILD → REVIEW` requires every work item settled, the integration branch
  green, every acceptance criterion covered by a passing test, and a build
  savepoint at the integration head.
- `DEPLOY_DESIGN → DEPLOY_EXECUTE` requires both an accepted deployment spec
  and recorded consent.
- `DEPLOY_REVIEW → DONE` requires the deployment demo to be accepted.
- `evaluate_transition` is total: every `(state, request)` pair returns
  without raising.

---

## 3. `effort.py`

```python
class Effort(IntEnum):
    TRIVIAL = 0; LOW = 1; STANDARD = 2; HIGH = 3; MAX = 4


PHASE_BASE_EFFORT: Mapping[Phase, Effort] = {
    Phase.DESIGN: Effort.HIGH,     # the user's requirement
    Phase.VISUAL_DESIGN: Effort.HIGH,
    Phase.BUILD:  Effort.LOW,      # the user's requirement
    Phase.REVIEW: Effort.HIGH,     # the user's requirement
    Phase.DEPLOY_DESIGN: Effort.HIGH,
    Phase.DEPLOY_EXECUTE: Effort.LOW,
    Phase.DEPLOY_REVIEW: Effort.HIGH,
    Phase.DEPLOY: Effort.LOW,
}

# attempt -> effort, for Phase 2's per-item escalation ladder (1-based attempts)
BUILD_LADDER: tuple[Effort, ...] = (
    Effort.LOW, Effort.LOW,
    Effort.STANDARD, Effort.STANDARD,
    Effort.HIGH, Effort.HIGH,
)
BUILD_LADDER_EXHAUSTED = len(BUILD_LADDER)   # attempt 7 → human gate


def effort_for_attempt(base: Effort, attempt: int) -> Effort:
    """Phase 2 escalation. Never lowers below base; saturates at HIGH.
    Raises EscalationExhausted past attempt 6 (1-based)."""


def forces_rotation(previous: Effort, current: Effort) -> bool:
    return current > previous


def triage_required_effort(findings: Sequence[FindingRef]) -> Effort:
    """Required execution effort for a set of triaged review findings: any
    CRITICAL -> MAX, else any HIGH -> HIGH, else any MEDIUM -> STANDARD,
    else LOW."""
```

---

## 4. `engine.py`

```python
EXIT_CODE_WIND_DOWN = 75
"""The *loop runners' shared "graceful wind-down" exit code: the engine ran
out of window capacity mid-item and stopped cleanly after writing its state,
so the item hands off to another engine instead of failing
(handoff-protocol.md §3). A domain constant because the meaning belongs to
the protocol, not to any one subprocess adapter."""


class EngineId(StrEnum):
    CLAUDELOOP = "claudeloop"; CODEXLOOP = "codexloop"
    CURSORLOOP = "cursorloop"; AGYLOOP = "agyloop"; QWENLOOP = "qwenloop"


class Capability(StrEnum):
    SAVEPOINTS = "savepoints"; UNWIND = "unwind"
    STRUCTURED_VERDICT = "structured_verdict"
    MID_RUN_PROMPT = "mid_run_prompt"; MID_RUN_MODEL = "mid_run_model"
    MID_RUN_EFFORT = "mid_run_effort"; ATTACHMENTS = "attachments"
    SLASH_COMMANDS = "slash_commands"; WEB_SEARCH = "web_search"
    SNAPSHOT = "snapshot"; SANDBOX = "sandbox"


class IsolationLevel(StrEnum):
    WORKTREE = "worktree"; CONTAINER = "container"; VM = "vm"


@dataclass(frozen=True, slots=True)
class EngineInvocation:
    argv: tuple[str, ...]
    achieved: Effort
    notes: str = ""


@dataclass(frozen=True, slots=True)
class EngineDescriptor:
    engine_id: EngineId
    binary: str
    min_version: str
    state_dir: str
    done_marker: str
    auth_env: tuple[str, ...]
    capabilities: frozenset[Capability]
    effort_projection: Mapping[Effort, EngineInvocation]
    session_verb: str
    isolation_flags: Mapping[IsolationLevel, tuple[str, ...]]
    cost_per_mtok_in: float
    cost_per_mtok_out: float
    context_window: int
    base_weight: int = 1
    supports_cwd_flag: bool = True   # False for a binary that rejects --cwd
    plan_flag: str | None = None     # None = bare positional; else the flag name (e.g. cursorloop's --plan)

    def invoke(self, effort: Effort) -> EngineInvocation:
        """Falls back to the highest projection at or below `effort` — the
        descriptor's own saturation point — rather than raising KeyError."""

    def saturates_at(self, effort: Effort) -> bool:
        return self.invoke(effort).achieved < effort


@dataclass(frozen=True, slots=True)
class JobRequirement:
    effort: Effort
    capabilities: frozenset[Capability] = frozenset()
    excluded: frozenset[EngineId] = frozenset()   # the "must differ" constraint
```

`supports_cwd_flag` and `plan_flag` exist because each engine's CLI was
verified against its actual `--help` output, not assumed: passing a flag a
binary doesn't have, or a positional path to a binary that wants a flag,
fails at argument parsing before the session ever starts.

---

## 5. `capacity.py`

Inherited from the `*loop` family, unchanged in spirit and in the one rule that
matters.

```python
@dataclass(frozen=True, slots=True)
class Available: ...

@dataclass(frozen=True, slots=True)
class WindowExhausted:
    resets_at: datetime | None = None
    rate_limit_type: str | None = None

@dataclass(frozen=True, slots=True)
class CreditsExhausted:
    can_purchase: bool = True
    # There is deliberately NO resets_at field here, and there never will be.
    # A credits balance has no clock. Only a human top-up changes it.

@dataclass(frozen=True, slots=True)
class AuthenticationFailed:
    detail: str = ""

CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed
```

---

## 6. `circuit.py`

```python
class CircuitState(StrEnum):
    CLOSED = "closed"; HALF_OPEN = "half_open"; OPEN = "open"


@dataclass(frozen=True, slots=True)
class DeadlineProbe:
    at: datetime

@dataclass(frozen=True, slots=True)
class BackoffProbe:
    next_at: datetime
    attempt: int

ProbeSchedule = DeadlineProbe | BackoffProbe


@dataclass(frozen=True, slots=True)
class Circuit:
    state: CircuitState
    capacity: CapacityState
    probe: ProbeSchedule | None
    consecutive_failures: int = 0
    ewma_failure: float = 0.0


def schedule_probe(capacity: CapacityState, *, now: datetime, attempt: int) -> ProbeSchedule | None:
    """The type system carries the rule: CreditsExhausted can only ever produce
    a BackoffProbe, never a DeadlineProbe — because there is no deadline.
    Available -> None (no probe needed). WindowExhausted with a known
    resets_at -> a DeadlineProbe jittered off that time (deterministically,
    seeded from the reset time and attempt so retries stay reproducible).
    WindowExhausted with no reset time, or CreditsExhausted, -> a backoff
    schedule capped at 5 or 30 minutes respectively. AuthenticationFailed ->
    None; waiting cannot fix credentials."""
```

### The one property test that matters most

```python
@given(capacity=capacity_states(), now=datetimes(), attempt=st.integers(0, 100))
def test_credits_never_produce_a_deadline(capacity, now, attempt):
    probe = schedule_probe(capacity, now=now, attempt=attempt)
    if isinstance(capacity, CreditsExhausted):
        assert not isinstance(probe, DeadlineProbe)
```

---

## 7. `rotation.py`

```python
@dataclass(frozen=True, slots=True)
class EngineRuntime:
    """The live state application/ assembles for one engine before a
    selection round: the static descriptor plus whatever changes call to
    call (circuit, install/auth checks)."""
    engine_id: EngineId
    descriptor: EngineDescriptor
    circuit: Circuit
    installed: bool
    conformance_ok: bool
    auth_valid: bool


@dataclass(frozen=True, slots=True)
class Candidate:
    engine_id: EngineId
    base_weight: int
    current: int
    order: int
    health_factor: float
    fidelity_factor: float
    cost_factor: float
    affinity_factor: float

    @property
    def effective_weight(self) -> int:
        """0 if the combined weight is non-positive; otherwise rounded but
        floored at 1. A positive weight must never round down to zero — a
        half-open probe on a base_weight-1 engine is 1 * 0.25 = 0.25, and a
        plain round() would make that 0, so the probe could never fire and
        the engine would stay open forever."""
        raw = (self.base_weight * self.health_factor * self.fidelity_factor
               * self.cost_factor * self.affinity_factor)
        if raw <= 0:
            return 0
        return max(1, round(raw))


@dataclass(frozen=True, slots=True)
class Selection:
    engine_id: EngineId
    candidates: tuple[Candidate, ...]     # updated SWRR state


def eligible(
    runtimes: Sequence[EngineRuntime], *, requirement: JobRequirement,
    allow_list: frozenset[EngineId] | None = None,
) -> tuple[EngineRuntime, ...]:
    """Filters out engines that aren't installed, don't pass conformance,
    have invalid auth, have an OPEN circuit, are in `requirement.excluded`,
    aren't on an explicit `allow_list`, or lack a required capability."""

def select(candidates: Sequence[Candidate]) -> Selection: ...      # smooth WRR
def health_factor(circuit: Circuit) -> float: ...
def fidelity_factor(descriptor: EngineDescriptor, requested: Effort) -> float: ...
def cost_factor(descriptor, *, median_cost: float, enabled: bool) -> float: ...
def affinity_factor(*, holds_warm_session: bool, rotation_forced: bool) -> float: ...
```

- `health_factor`: `1.0` closed (decaying with `ewma_failure`), `0.25`
  half-open, `0.0` open. Half-open is a *quarter*, not a half (ADR-0005): a
  circuit under test should win a round only when the alternatives are
  genuinely worse, not on even footing with a healthy engine.
- `fidelity_factor`: `1.0` at the requested tier, `0.7` one tier short,
  `0.5` two-or-more tiers short — an engine that saturates far below what was
  asked for is worse than one that just misses.
- `affinity_factor`: `2.0` for a warm session unless rotation is forced
  (then `1.0`) — this is what keeps an ordinary retry from becoming a
  handoff on every retry.

### Properties

| Property | Statement |
|---|---|
| **No starvation** | Over `sum(effective_weight)` consecutive selections, every candidate with `effective_weight > 0` is selected at least once |
| **Weight fidelity** | Selection counts converge to weight ratios within ±1 over any full period |
| **Smoothness** | No candidate is selected twice consecutively while another with `effective_weight > 0` has gone unselected longer |
| **Determinism** | Identical candidate state produces an identical selection |
| **Totality** | `select` raises `NoEligibleEngine` iff every `effective_weight` is 0, or if the input is empty |
| **Unique identity** | `select` raises `ValueError` if two candidates share an `engine_id` |
| **Exclusion honored** | An engine in `requirement.excluded` is never returned |

---

## 8. `ledger.py`

```python
class EventKind(StrEnum):
    SESSION_SEEDED = "SessionSeeded"; TURN_REQUESTED = "TurnRequested"
    TURN_COMPLETED = "TurnCompleted"; TOOL_INVOKED = "ToolInvoked"
    FILE_EDITED = "FileEdited"; VERDICT_RENDERED = "VerdictRendered"
    CAPACITY_REJECTED = "CapacityRejected"
    QUESTION_ASKED = "QuestionAsked"; ANSWER_GIVEN = "AnswerGiven"
    DECISION_RECORDED = "DecisionRecorded"; ASSUMPTION_STATED = "AssumptionStated"
    FINDING_RAISED = "FindingRaised"; FINDING_RESOLVED = "FindingResolved"
    ARTIFACT_PRODUCED = "ArtifactProduced"; SAVEPOINT_CREATED = "SavePointCreated"
    HANDOFF_INITIATED = "HandoffInitiated"; HANDOFF_ACCEPTED = "HandoffAccepted"
    PHASE_TRANSITIONED = "PhaseTransitioned"; BUDGET_SPENT = "BudgetSpent"
    VISUAL_DESIGN_OPTED_IN = "VisualDesignOptedIn"
    VISUAL_DESIGN_DECLINED = "VisualDesignDeclined"
    VISUAL_DESIGN_ACCEPTED = "VisualDesignAccepted"
    VISUAL_DESIGN_WAIVED = "VisualDesignWaived"
    DEPLOYMENT_OPTED_IN = "DeploymentOptedIn"; DEPLOYMENT_DECLINED = "DeploymentDeclined"


CLOSABLE: frozenset[EventKind] = frozenset({
    EventKind.QUESTION_ASKED, EventKind.DECISION_RECORDED,
    EventKind.ASSUMPTION_STATED, EventKind.FINDING_RAISED,
})

CLOSES: Mapping[EventKind, EventKind] = {
    EventKind.ANSWER_GIVEN:    EventKind.QUESTION_ASKED,
    EventKind.FINDING_RESOLVED: EventKind.FINDING_RAISED,
}


class Provenance(StrEnum):
    TRUSTED = "trusted"      # vibey itself, the developer
    AGENT = "agent"          # an engine's own output
    UNTRUSTED = "untrusted"  # web, dependencies, issue text — data, never instruction


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    event_id: UUID; project_id: UUID; cycle: int; phase: Phase
    seq: int; kind: EventKind; engine_id: EngineId | None
    job_id: UUID | None; causation_id: UUID | None; correlation_id: UUID
    provenance: Provenance; produced_at: datetime
    payload: Mapping[str, object]; digest: str


def canonical_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()

def digest_event(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()

def digest_range(events: Sequence[LedgerEvent]) -> str:
    """Order-sensitive Merkle-ish fold. Rule R6 depends on this."""
    h = hashlib.sha256()
    for e in sorted(events, key=lambda x: x.seq):
        h.update(str(e.seq).encode()); h.update(b"\x00"); h.update(e.digest.encode())
    return h.hexdigest()


def open_items(events: Sequence[LedgerEvent], kind: EventKind) -> tuple[str, ...]:
    """Ids opened by `kind` and not yet closed or superseded, in the order
    they were opened. Raises ValueError if `kind` is not in CLOSABLE. A
    DecisionRecorded event whose payload carries a `supersedes` id closes
    that prior decision the same way an explicit closing event would."""
```

---

## 9. `handoff.py` and `noloss.py`

Specified in full in [handoff-protocol.md](handoff-protocol.md). `handoff.py`
defines the envelope and brief types; `noloss.py` is the pure gate that
verifies a brief against the ledger before a handoff is allowed to complete.

```python
# handoff.py
class HandoffReason(StrEnum):
    ROTATION = "rotation"; CAPACITY = "capacity"; ESCALATION = "escalation"
    FAILURE = "failure"; PHASE_TRANSITION = "phase_transition"; OPERATOR = "operator"


class GateMode(StrEnum):
    STRICT = "strict"; FULL_TRANSCRIPT = "full_transcript"
    HUMAN = "human"; FORCED = "forced"


class GateRule(StrEnum):
    R1_REMAINING = "R1"; R2_QUESTIONS = "R2"; R3_DECISIONS = "R3"
    R4_ASSUMPTIONS = "R4"; R5_FINDINGS = "R5"; R6_RANGE = "R6"
    R7_ARTIFACTS = "R7"; R8_BUDGET = "R8"; R9_CONSTRAINTS = "R9"
    R10_CONTAINMENT = "R10"


@dataclass(frozen=True, slots=True)
class Violation:
    rule: GateRule
    item_id: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class GateResult:
    ok: bool
    mode: GateMode
    attempts: int
    violations: tuple[Violation, ...]
    rules_run: tuple[GateRule, ...]


# The refs a HandoffBrief is built from, and closes against the ledger:
@dataclass(frozen=True, slots=True)
class DecisionRef:
    decision_id: str
    restatement: str

@dataclass(frozen=True, slots=True)
class AssumptionRef:
    assumption_id: str
    restatement: str

@dataclass(frozen=True, slots=True)
class QuestionRef:
    question_id: str
    text: str
    blocking: bool

@dataclass(frozen=True, slots=True)
class RemainingItem:
    text: str
    item_id: str | None = None

@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_id: str
    path: str


@dataclass(frozen=True, slots=True)
class HandoffBrief:
    objective: str
    constraints: tuple[str, ...]
    decisions: tuple[DecisionRef, ...]
    assumptions: tuple[AssumptionRef, ...]
    done: tuple[str, ...]
    remaining: tuple[RemainingItem, ...]
    open_questions: tuple[QuestionRef, ...]
    open_findings: tuple[FindingRef, ...]
    artifacts: tuple[ArtifactRef, ...]
    invariants: tuple[str, ...]
    style_rules: tuple[str, ...]
    next_action: str


@dataclass(frozen=True, slots=True)
class LedgerRef:
    """The ledger range a brief was verified against — what R6 checks."""
    uri: str
    from_seq: int
    to_seq: int
    event_count: int
    digest: str


@dataclass(frozen=True, slots=True)
class RepoState:
    branch: str
    head_sha: str
    worktree_path: str
    dirty_paths: tuple[str, ...]
    last_savepoint: str | None
    integration_branch: str | None


@dataclass(frozen=True, slots=True)
class HandoffEnvelope:
    """The full record persisted (to disk, in the receiving worktree) every
    time work moves from one engine to another."""
    schema_version: int
    handoff_id: UUID
    project_id: UUID
    cycle: int
    phase: Phase
    from_engine: EngineId | None
    to_engine: EngineId
    reason: HandoffReason
    produced_at: datetime
    brief: HandoffBrief
    repo_state: RepoState
    ledger_ref: LedgerRef
    budget: BudgetSnapshot          # = budget.py's BudgetLedger, re-exported
    gate: GateResult
```

```python
# noloss.py
def verify(
    *, ledger, brief, ref, budget, spec_constraints=(), mode=GateMode.STRICT, attempts=1,
) -> GateResult:
    """Pure. No model call. This function is the reason rotation is safe."""
```

`verify` runs ten independent checks, each producing zero or more
`Violation`s, keyed by the `GateRule` it enforces:

| Rule | Checks |
|---|---|
| R1 | Every item in the latest `VerdictRendered` event's `remaining_work` appears in `brief.remaining` |
| R2 | Every open `QuestionAsked` id (per `open_items`) appears in `brief.open_questions` |
| R3 | Every open `DecisionRecorded` id appears in `brief.decisions` |
| R4 | Every open `AssumptionStated` id appears in `brief.assumptions` |
| R5 | Every open `FindingRaised` id appears in `brief.open_findings` |
| R6 | `ref.digest`, `ref.event_count`, and `ref.to_seq` all match the ledger range actually supplied |
| R7 | Every artifact referenced by an open item appears in `brief.artifacts` |
| R8 | The ledger's summed `BudgetSpent` dollars/turns match `budget.dollars_spent` / `budget.turns_spent` |
| R9 | Every hard `spec_constraints` string appears in `brief.constraints` |
| R10 | No brief text field contains a phrase from the containment denylist (tool grants, permission changes, acceptance-criteria mutation, prompt-injection phrases like "ignore previous instructions", `sudo`) |

Under `GateMode.FULL_TRANSCRIPT`, R1–R5, R7, and R9 are auto-satisfied
(closure over the brief no longer means anything once the whole ledger range
is inlined into the prompt) — but R6, R8, and R10 still run, because they
check facts about the range and the brief's containment, not brief
completeness. R10 is the security control from the architecture threat model:
an untrusted brief field is data the *next* engine reads, so it is scanned
for injection before that handoff completes.

---

## 10. `job.py`, `spec.py`, `review.py`, `budget.py`

```python
# job.py
class JobState(StrEnum):
    READY="ready"; LEASED="leased"; SUCCEEDED="succeeded"; FAILED="failed"
    AWAITING_HUMAN="awaiting_human"; AWAITING_CAPACITY="awaiting_capacity"
    CANCELLED="cancelled"

class FailureClass(StrEnum):
    CAPACITY="capacity"   # opens the circuit
    ENGINE="engine"       # opens after 3
    WORK="work"           # the code is wrong — circuit untouched
    VIBEY="vibey"         # our bug — circuit untouched

def backoff(attempt: int, *, base=timedelta(seconds=2), cap=timedelta(minutes=15)) -> timedelta: ...
def idempotency_key(project_id: UUID, cycle: int, kind: str, subject: str) -> str: ...


# spec.py
class ConstraintKind(StrEnum):
    HARD = "hard"; SOFT = "soft"

@dataclass(frozen=True, slots=True)
class Constraint:
    text: str
    kind: ConstraintKind

@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    criterion_id: str; given: str; when: str; then: str; fit: str

@dataclass(frozen=True, slots=True)
class NonFunctionalRequirement:
    nfr_id: str; attribute: str
    scale: str; meter: str; must: str; wish: str | None; fit_criterion: str
    # Planguage. "fast" is not an NFR; a scale and a meter are.

@dataclass(frozen=True, slots=True)
class DesignSpec:
    objective: str
    constraints: tuple[Constraint, ...]        # each hard|soft — R9 checks the hard ones
    non_goals: tuple[str, ...]
    criteria: tuple[AcceptanceCriterion, ...]
    nfrs: tuple[NonFunctionalRequirement, ...]
    walking_skeleton: str

    def is_buildable(self) -> tuple[str, ...]:
        """Returns violations; empty means the DESIGN → BUILD guard can pass."""

    def hard_constraints(self) -> tuple[str, ...]:
        """The text of every HARD constraint — what noloss.py's R9 checks
        a handoff brief against."""


# review.py
class Severity(StrEnum): CRITICAL="critical"; HIGH="high"; MEDIUM="medium"; LOW="low"
class Ambiguity(StrEnum): CLEAR="clear"; NEEDS_CLARIFICATION="needs_clarification"
class UserVerdict(StrEnum): ACCEPT="accept"; CHANGES="changes"; CANCEL="cancel"

@dataclass(frozen=True, slots=True)
class FindingRef:
    """A pointer to a FindingRaised ledger event, carrying just enough to
    route the review loop-back decision without re-reading the ledger."""
    finding_id: str
    severity: Severity
    ambiguity: Ambiguity

@dataclass(frozen=True, slots=True)
class AssumptionDelta:
    assumption_id: str; text: str; seq: int

@dataclass(frozen=True, slots=True)
class FindingDelta:
    finding_id: str; severity: Severity; ambiguity: Ambiguity
    text: str; seq: int; resolved: bool = False

@dataclass(frozen=True, slots=True)
class DeltasReport:
    assumptions: tuple[AssumptionDelta, ...]
    findings: tuple[FindingDelta, ...]

def render_deltas_markdown(report: DeltasReport) -> str: ...   # deltas.md
def render_demo_markdown(spec: DesignSpec, *, evidence=None) -> str: ...   # DEMO.md, per criterion
def render_run_it_script(commands: Sequence[str] = ()) -> str: ...   # run-it.sh
def render_walkthrough_markdown(*, spec=None, summary="", work_items=()) -> str: ...   # walkthrough.md

def classify_finding_severity(text: str, category: str = "") -> Severity:
    """Keyword-based triage: security/vulnerability/injection/data-loss/
    corrupt/leak/critical/invariant -> CRITICAL; defect/missing/broken/
    fails/failure/regression/crash/error/high -> HIGH; cosmetic/nit/typo/
    doc/comment/formatting/low -> LOW; otherwise MEDIUM."""

def check_clear_conditions(text: str, *, spec=None, decisions=()) -> tuple[bool, str]:
    """Evaluates review.py's 4 conjunctive conditions for Ambiguity.CLEAR:
    (1) the desired end state is stated unambiguously, (2) it maps to an
    existing or obviously-testable acceptance criterion, (3) it implies no
    new NFR or architectural constraint, (4) it does not contradict a
    recorded decision's chosen alternative."""

def triage_finding(finding_id: str, text: str, *, category="", spec=None, decisions=()) -> FindingRef:
    """Combines classify_finding_severity and check_clear_conditions into
    the FindingRef next_phase_after_review actually routes on."""


# budget.py
@dataclass(frozen=True, slots=True)
class BudgetLedger:
    turns_spent: int; dollars_spent: float
    max_turns: int | None; max_dollars: float | None

    @property
    def any_exhausted(self) -> bool: ...
    def would_exceed(self, projected: float) -> bool: ...
    def spend(self, *, turns=0, dollars=0.0) -> BudgetLedger: ...
```

`would_exceed` is checked **before** an effort escalation, not after — the
escalation ladder is the mechanism most likely to cause a cost snowball, so the
cap is evaluated on the projection, not the outcome.

---

## 11. `visual.py` and `media.py`

The visual-design interstitial's inventory, and the media-provider selection
that will eventually fill it in. Both are shape-only: generation, providers,
and moderation are separate, not-yet-implemented milestones (tasks
5.8–5.11); these modules only cover *what a complete inventory looks like*
and *which provider, if any, is eligible*.

```python
# visual.py
class MediaModality(StrEnum):
    IMAGE = "image"; AUDIO = "audio"; VIDEO = "video"

class SurfaceAction(StrEnum):
    CREATE = "create"; UPDATE = "update"

@dataclass(frozen=True, slots=True)
class MediaManifestEntry:
    asset_key: str
    modality: MediaModality
    prompt: str

@dataclass(frozen=True, slots=True)
class ScreenSurface:
    screen_id: str
    name: str
    action: SurfaceAction
    responsive_states: tuple[str, ...]
    accessibility_requirements: tuple[str, ...]
    media_manifest: tuple[MediaManifestEntry, ...]

@dataclass(frozen=True, slots=True)
class VisualInventory:
    surfaces: tuple[ScreenSurface, ...]

    def is_complete(self) -> tuple[str, ...]:
        """Returns violations; empty means the inventory can enter
        visual.plan. Requires at least one surface, and every surface to
        carry responsive states, accessibility requirements, and media
        manifest entries."""
```

```python
# media.py
@dataclass(frozen=True, slots=True)
class MediaProviderDescriptor:
    provider_id: str
    modalities: frozenset[MediaModality]        # MediaModality imported from visual.py
    reference_input_limit: int
    output_formats: frozenset[str]
    region: str
    retention_policy: str
    safety_policy: str
    cost_per_unit: float
    long_running: bool
    external: bool   # False: local/self-hosted, tried first. True: hosted fallback.

@dataclass(frozen=True, slots=True)
class MediaRequirement:
    modality: MediaModality
    allow_external: bool = False
    max_cost_per_unit: float | None = None

@dataclass(frozen=True, slots=True)
class MediaProviderRuntime:
    descriptor: MediaProviderDescriptor
    circuit_open: bool = False

def eligible(runtimes: Sequence[MediaProviderRuntime], *, requirement: MediaRequirement) -> tuple[MediaProviderRuntime, ...]:
    """Filters out providers with an open circuit, that lack the required
    modality, that are external when external isn't allowed, or that exceed
    a cost ceiling."""

@dataclass(frozen=True, slots=True)
class MediaCandidate:
    provider_id: str
    base_weight: int
    current: int
    order: int

    @property
    def effective_weight(self) -> int:
        return max(0, self.base_weight)

@dataclass(frozen=True, slots=True)
class MediaSelection:
    provider_id: str
    candidates: tuple[MediaCandidate, ...]   # updated SWRR state

def select(candidates: Sequence[MediaCandidate]) -> MediaSelection:
    """Smooth Weighted Round Robin, one modality at a time — the same
    algorithm as rotation.py's engine selection, reimplemented rather than
    shared because the two rotate different identity types and must be free
    to diverge (media has no capacity/circuit-breaker concept yet). Raises
    NoEligibleEngine on an empty candidate list or an all-zero-weight set;
    raises ValueError on a duplicate provider_id."""
```

The domain never imports an SDK or knows a provider/model name. It evaluates
capability, policy, region, health, and budget facts supplied by `application/`;
the infrastructure adapter performs the actual generation.

---

## 12. `briefing.py`

```python
def build_deterministic_brief(
    events: Sequence[LedgerEvent], *,
    objective="See the accepted spec in .vibey/context/spec.md.",
    spec_constraints=(), invariants=(), style_rules=(),
) -> HandoffBrief:
    """vibey's own floor producer for a HandoffBrief (handoff-protocol.md
    §6.5, option 4). Built directly from domain/projections.py's
    build_open_items and build_decision_log over the same ledger the no-loss
    gate checks against, so it always passes the gate by construction — no
    model call, less fluent than an LLM-written brief, but never lossy. This
    is what makes "all engines are down" a degraded-quality scenario rather
    than a data-loss one."""
```

`next_action` is taken from the first item in the latest `VerdictRendered`
event's `remaining_work`, or `"Review and accept."` if there is none;
`decisions` includes only decision refs that are not yet superseded.

---

## 13. `plan.py`

BUILD decomposition: the work-item graph and its two structural rules
(task 6.1, phase-protocols.md §2.1). `build.decompose` turns an accepted spec
into a dependency-ordered work-item graph.

```python
@dataclass(frozen=True, slots=True)
class VerificationSpec:
    """Exactly how a work item's completion will be checked."""
    commands: tuple[str, ...]
    criteria_checked: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class WorkItem:
    item_id: str
    title: str
    acceptance_ids: tuple[str, ...]
    depends_on: tuple[str, ...]
    est_effort: Effort
    files_touched_hint: tuple[str, ...]
    verification: VerificationSpec

def validate_decomposition(
    items: Sequence[WorkItem], *, criteria_ids: Sequence[str], walking_skeleton_item_id: str,
) -> tuple[str, ...]:
    """Returns violations; empty means the decomposition can enter BUILD.
    Checks: no duplicate item_id; every depends_on target exists; every
    acceptance criterion maps to >= 1 work item (an unmapped criterion is a
    decomposition bug, not a judgment call); the named walking-skeleton item
    exists and has no dependencies — it goes first, alone, and must go green
    before anything else starts."""

def build_parallelism(*, config_parallelism: int | None, eligible_items: int, cpu_count: int) -> int:
    """min(config, eligible_items * 2, cpu_count). config_parallelism comes
    from phases.build.parallelism in vibey.toml (None means the default of
    4); eligible_items and cpu_count are supplied by the caller — the domain
    does not read them from the environment."""
```

---

## 14. `projections.py`

Pure projections over a replayed event range (architecture-and-roadmap.md
§4): every one of them is derived and disposable — rebuildable from the
ledger alone — which is what makes it safe to materialize any of them for
query speed without ever becoming a second source of truth.

```python
@dataclass(frozen=True, slots=True)
class OpenItemsView:
    questions: tuple[str, ...]
    decisions: tuple[str, ...]
    assumptions: tuple[str, ...]
    findings: tuple[str, ...]

def build_open_items(events: Sequence[LedgerEvent]) -> OpenItemsView: ...


@dataclass(frozen=True, slots=True)
class DecisionLogEntry:
    """ADR-shaped: every decision ever recorded, open or superseded."""
    decision_id: str; title: str; choice: str; rationale: str
    alternatives: tuple[str, ...]; superseded_by: str | None; seq: int

def build_decision_log(events: Sequence[LedgerEvent]) -> tuple[DecisionLogEntry, ...]: ...


@dataclass(frozen=True, slots=True)
class CostReportEntry:
    phase: Phase; engine_id: EngineId | None; turns: int; dollars: float

def build_cost_report(events: Sequence[LedgerEvent]) -> tuple[CostReportEntry, ...]:
    """Sums BudgetSpent events, grouped by (phase, engine_id)."""


@dataclass(frozen=True, slots=True)
class WorkLedgerEntry:
    """Per work-thread status, keyed by correlation_id — the closest thing
    the event log has to a stable work-item identifier. Narrower than the
    full work_item table (which additionally tracks branch/worktree/
    verification state); answers "is this thread of work done, and what's
    left" from replay alone."""
    correlation_id: str; complete: bool; remaining_work: tuple[str, ...]; last_seq: int

def build_work_ledger(events: Sequence[LedgerEvent]) -> tuple[WorkLedgerEntry, ...]: ...

def build_deltas(events: Sequence[LedgerEvent]) -> DeltasReport:
    """Every AssumptionStated and FindingRaised event in the run, so neither
    can be silently omitted from the review; findings carry their resolved
    state from any matching FindingResolved event."""

def answer_why_question(events: Sequence[LedgerEvent], question: str) -> str:
    """Answers a developer's free-text question by keyword-matching it
    against recorded DecisionRecorded and AssumptionStated events, so the
    answer explains the rationale actually on the ledger rather than
    inventing a new one from a fresh model call."""
```

---

## 15. `config.py`

Parsing and validation of the `vibey.toml` schema — see
[configuration reference](../reference/configuration.md) for the full field
list with defaults. Pure: this module accepts already-loaded TOML text or a
dict and returns either a validated `VibeyConfig` or raises `ConfigError`; it
never touches the filesystem — reading the file is an infrastructure concern.

```python
VALID_ISOLATION_LEVELS = ("worktree", "container", "vm")
VALID_EFFORTS = ("trivial", "low", "standard", "high", "max")
DEFAULT_ENGINES = ("claudeloop", "codexloop", "cursorloop", "agyloop")
KNOWN_ENGINES = (*DEFAULT_ENGINES, "qwenloop")

class ConfigError(VibeyError):
    def __init__(self, path: str, message: str) -> None: ...

@dataclass(frozen=True, slots=True)
class ProjectConfig:
    name: str; repo: str = "."; max_cycles: int = 10; strict_loopback: bool = False

@dataclass(frozen=True, slots=True)
class IsolationConfig:
    level: str = "worktree"; allow_push: bool = False; egress: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class BudgetConfig:
    max_dollars_per_cycle: float | None = None
    max_dollars_total: float | None = None
    max_turns_per_item: int | None = None

@dataclass(frozen=True, slots=True)
class EnginesConfig:
    enabled: tuple[str, ...] = DEFAULT_ENGINES
    weights: dict[str, int] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class PhaseConfig:
    effort: str = "standard"
    engines: tuple[str, ...] | None = None
    parallelism: int | None = None

@dataclass(frozen=True, slots=True)
class PhasesConfig:
    design: PhaseConfig  # default effort="high"
    build: PhaseConfig   # default effort="low"
    review: PhaseConfig  # default effort="high"

@dataclass(frozen=True, slots=True)
class ProvisionConfig:
    plugins: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class DeployConfig:
    enabled: bool = False; target: str = "azure"; iac: str = "bicep"

@dataclass(frozen=True, slots=True)
class FeaturesConfig:
    qwenloop: bool = False

@dataclass(frozen=True, slots=True)
class QwenloopConfig:
    backend: str = "auto"   # one of "auto", "llama.cpp", "vllm"
    portable_profile: str = "qwen2.5-coder-14b-q5-k-m"
    nvidia_profile: str = "qwen2.5-coder-14b-bf16"
    idle_timeout_seconds: int = 900
    startup_timeout_seconds: int = 180
    context_window: int = 32_768

@dataclass(frozen=True, slots=True)
class VibeyConfig:
    project: ProjectConfig
    isolation: IsolationConfig = field(default_factory=IsolationConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    engines: EnginesConfig = field(default_factory=EnginesConfig)
    phases: PhasesConfig = field(default_factory=PhasesConfig)
    provision: ProvisionConfig = field(default_factory=ProvisionConfig)
    deploy: DeployConfig = field(default_factory=DeployConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    qwenloop: QwenloopConfig = field(default_factory=QwenloopConfig)

def parse_config(data: dict[str, Any]) -> VibeyConfig:
    """Raises ConfigError on the first violation found. `qwenloop` may only
    be requested (in engines.enabled or any phase's engines list) once
    features.qwenloop is true; conversely, turning features.qwenloop on
    without an explicit engines.enabled list adds "qwenloop" to the default
    engine set automatically."""

def load_config_from_string(text: str) -> VibeyConfig: ...
```

---

## 16. `provision.py`

Agent-surface provisioning content rules (task 6.3, ADR-0011): one source of
truth for the non-negotiables/plugins/context block, materialized
idempotently into every engine's router file (`CLAUDE.md`, `AGENTS.md`,
`CURSOR.md`, `GEMINI.md`, `QWEN.md`). Pure content generation and the
marker-delimited merge that preserves hand-written guidance outside vibey's
block; the actual filesystem/git I/O lives in `infrastructure/provision/`.

```python
BEGIN_MARKER = "<!-- vibey:begin -->"
END_MARKER = "<!-- vibey:end -->"

class RouterFile(StrEnum):
    """Agent guidance surfaces, including qwenloop's local-agent router."""
    CLAUDE = "CLAUDE.md"; AGENTS = "AGENTS.md"; CURSOR = "CURSOR.md"
    GEMINI = "GEMINI.md"; QWEN = "QWEN.md"

@dataclass(frozen=True, slots=True)
class ProvisionSpec:
    non_negotiables: tuple[str, ...]
    plugins: tuple[str, ...]

def render_block(spec: ProvisionSpec) -> str:
    """Renders the marker-delimited, generated block: non-negotiables,
    skill plugins, and a pointer to .vibey/context/."""

def merge_router(existing: str | None, block: str) -> str:
    """Preserves any hand-written content outside vibey's markers; replaces
    only vibey's own block between BEGIN_MARKER/END_MARKER, or appends the
    block to unmarked existing content (or returns it standalone if there is
    no existing content)."""

def content_digest(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def needs_write(existing: str | None, rendered: str) -> bool:
    """The idempotence check (ADR-0011): true only when writing would
    actually change the file, so re-provisioning with correct digests
    already present writes nothing."""
```

---

## 17. `worktree.py`

Pure naming rules for BUILD work-item worktrees (task 6.2): no I/O, just the
deterministic path/branch scheme the infrastructure worktree manager uses,
kept pure so the manager and any future caller (e.g. a status report) never
disagree about where a work item's worktree lives.

```python
def validate_item_id(item_id: str) -> None:
    """Raises ValueError unless item_id is 1-64 chars, lowercase
    alphanumeric and hyphens, starting with alphanumeric."""

def worktree_subpath(cycle: int, item_id: str) -> str:
    return f".vibey/worktrees/{cycle}/{item_id}"

def branch_name(cycle: int, item_id: str) -> str:
    return f"vibey/{cycle}/{item_id}"
```

Returns a relative path string rather than a `pathlib.Path`: `domain/`
forbids `pathlib` (checked by `test_domain_purity.py`), so joining this onto
a repo root is the infrastructure layer's job.

---

## 18. `verbosity.py`

Resolving how loud the process should be, from CLI flags. Pure: no logging
library, no I/O — the ladder is a domain decision because it has to mean the
same thing everywhere; an operator who learns `-vv` on one runner should not
get something different from the next one.

```python
VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

class Verbosity(IntEnum):
    """QUIET and NORMAL differ only in level. The three DEBUG tiers differ in
    *scope*: our own logs, then third-party libraries, then full payloads —
    because "more detail" past DEBUG is not a level, it is a wider net."""
    QUIET = -1; NORMAL = 0; VERBOSE = 1; TRACE = 2; FIREHOSE = 3


@dataclass(frozen=True, slots=True)
class LogPlan:
    """The resolved logging intent a composition root acts on."""
    level: str
    include_third_party: bool
    include_payloads: bool


def parse_verbosity(*, verbose: int = 0, quiet: bool = False) -> Verbosity:
    """Raises ValueError if --quiet and --verbose are both set."""

def resolve_log_plan(*, verbose: int = 0, quiet: bool = False, log_level: str | None = None) -> LogPlan:
    """An explicit --log-level always wins over the -v count — naming a
    level and having it silently overridden by a count (possibly set in an
    alias) would be more surprising than honouring it. The count still
    widens scope independently, so `--log-level WARNING -vvv` is a
    legitimate way to ask for warnings from everything: include_third_party
    from TRACE and up, include_payloads from FIREHOSE."""
```

---

## 19. Security primitives: `command_guard.py`, `scope_guard.py`, `prompt_shield.py`

Three self-contained, pure defensive modules with full unit coverage. **None
of them are constructed anywhere in `bootstrap.py`** — see
[SECURITY.md](../../SECURITY.md) for the current disclosure of what this
means for the guarantees vibey actually provides today; do not rely on any
of them being enforced until that changes.

```python
# command_guard.py — destructive-command prevention
@dataclass(slots=True, frozen=True)
class BlockedMatch:
    command: str; rule_id: str; description: str

class DestructiveCommandBlocked(Exception):
    def __init__(self, match: BlockedMatch) -> None: ...

def scan_command(command: Sequence[str] | str) -> BlockedMatch | None:
    """Matches the command string (argv joined with spaces if given a
    sequence) against a fixed table of regexes: git hard reset, git force
    push, git branch -D on main/master, rm -rf on / or ~, mkfs, dd of=/dev/*,
    recursive chmod on /, shutdown/reboot/poweroff, a shell fork bomb
    pattern, and SQL DROP DATABASE/TABLE. Returns the first match or None."""

class CommandSecurityPolicy:
    def is_allowed(self, command: Sequence[str] | str) -> bool: ...
    def check_command(self, command: Sequence[str] | str) -> None:
        """Raises DestructiveCommandBlocked on a match."""


# scope_guard.py — mutation scope enforcement
class ScopeViolation(Exception):
    def __init__(self, path: str, reason: str) -> None: ...

class MutationScope:
    """Enforces that mutations stay within declared scope boundaries."""
    def __init__(self, *, worktree_root: str, allowed_paths: Sequence[str] | None = None,
                 allow_new_files: bool = True) -> None: ...
    def is_path_allowed(self, path: str) -> bool: ...
    def validate_path(self, path: str) -> str:
        """Returns the normalized relative path, or raises ScopeViolation
        for path traversal, an absolute path outside worktree_root, a
        sensitive path (.git/, secrets.json, id_rsa/id_ed25519/id_ecdsa,
        .env*), or a path outside the declared allowed_paths."""
    def validate_batch(self, paths: Sequence[str]) -> list[str]: ...


# prompt_shield.py — untrusted-content framing and sanitization
@dataclass(slots=True, frozen=True)
class ShieldedPrompt:
    framed_text: str; nonce: str; sanitized_input: str

class PromptShield:
    def sanitize_text(self, text: str) -> str:
        """Strips ANSI escape sequences and non-whitespace control chars."""
    def is_suspicious_injection(self, text: str) -> bool:
        """Regex match against common injection phrases ("ignore previous
        instructions", "system prompt override", "act as root", …)."""
    def frame_untrusted_input(self, text: str, label: str = "untrusted_content",
                               nonce: str | None = None) -> ShieldedPrompt:
        """Sanitizes the text, escapes any attempted closing-tag breakout
        for the given label, and wraps it in a nonce-tagged delimiter pair
        with an explicit "treat this as data" directive."""
```

---

## 20. `deployment.py`

Immutable `DeploymentSpec`, consent verification, and failure-routing policy
for the ④–⑥ deployment stage set (task 10.2).

```python
@dataclass(slots=True, frozen=True)
class AzureTargetScope:
    tenant_id: str; subscription_id: str; resource_group: str
    environment: str; region: str; tags: Mapping[str, str] = field(default_factory=dict)

    def digest(self) -> str:
        """Deterministic SHA256 of tenant/subscription/resource-group/environment."""

@dataclass(slots=True, frozen=True)
class IdentityAuthority:
    identity_type: str; principal_id: str; approved_roles: Sequence[str] = ()

@dataclass(slots=True, frozen=True)
class TopologyConfig:
    service_type: str; iac_provider: str; sku: str
    instances: int = 1; ingress_enabled: bool = True; tls_enabled: bool = True

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
    spec_id: str; version: str
    target_scope: AzureTargetScope; identity: IdentityAuthority
    topology: TopologyConfig; recovery_policy: RecoveryPolicy
    verification: VerificationContract; cost_boundary: CostBoundary
    secret_references: Sequence[str] = ()

    def scope_digest(self) -> str: ...
    def validate(self) -> list[str]:
        """Every field-presence and non-negative-cost check, plus: each
        secret_references entry must use an approved Key Vault reference
        scheme (@microsoft.keyvault, keyvault:, vault:, ref:, kv:) — a raw
        secret value or unrecognized scheme is a validation error, not a
        silently accepted string."""
    def is_valid(self) -> bool: ...


@dataclass(slots=True, frozen=True)
class DeploymentConsent:
    consent_id: str; target_scope_digest: str
    granted_by: str; granted_at: datetime
    explicit_mutation_authorized: bool = True

    def matches_spec(self, spec: DeploymentSpec) -> bool:
        return self.explicit_mutation_authorized and self.target_scope_digest == spec.scope_digest()


class DeploymentFailureClass(StrEnum):
    TRANSIENT_CAPACITY = "transient_capacity"; IDEMPOTENT_CONFLICT = "idempotent_conflict"
    CAP_EXHAUSTED = "cap_exhausted"; MISSING_AUTHORITY = "missing_authority"
    POLICY_DENIAL = "policy_denial"; AMBIGUOUS_CONFIGURATION = "ambiguous_configuration"
    DESTRUCTIVE_DATA_MIGRATION = "destructive_data_migration"
    RECOVERY_OUTSIDE_RUNBOOK = "recovery_outside_runbook"; APPLICATION_DEFECT = "application_defect"

class DeploymentRoute(StrEnum):
    STAY_IN_EXECUTE = "stay_in_execute"; ENTER_REVIEW = "enter_review"
    ROUTE_TO_DESIGN = "route_to_design"; ROUTE_TO_DEPLOY_DESIGN = "route_to_deploy_design"

def classify_deployment_failure(failure_class: DeploymentFailureClass) -> DeploymentRoute:
    """Per ADR-0013: transient capacity or an idempotent conflict -> stay in
    DEPLOY_EXECUTE and retry; an application defect -> back to DESIGN;
    everything else -> DEPLOY_REVIEW for a human decision."""


class ChangeAction(StrEnum):
    CREATE = "create"; MODIFY = "modify"; DELETE = "delete"; NO_CHANGE = "no_change"

@dataclass(slots=True, frozen=True)
class NormalizedResourceChange:
    resource_id: str; resource_type: str; action: ChangeAction
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

def evaluate_iac_plan(changes, cost_boundary) -> PlanEvaluation:
    """Not safe for automated apply if any change is a DELETE, or if the
    summed estimated monthly cost exceeds cost_boundary.max_monthly_budget_usd."""


class DeploymentLadderDecision(StrEnum):
    RETRY = "retry"; ROLLBACK = "rollback"; HALT_AND_TRIAGE = "halt_and_triage"

@dataclass(slots=True, frozen=True)
class DeploymentAttemptRecord:
    attempt_number: int; elapsed_seconds: float; total_spent_usd: float
    last_failure_class: DeploymentFailureClass | None = None

def evaluate_retry_ladder(attempt, spec) -> tuple[DeploymentLadderDecision, str]:
    """Halts to triage over the dollar cap, past a 1800s elapsed cap, or
    past max_rollback_attempts + 1 total attempts. Otherwise: a transient
    failure class retries with backoff; any other failure rolls back if
    recovery_policy.auto_rollback_on_health_failure, else halts to triage."""


class ExposureType(StrEnum):
    REVISION = "revision"; SLOT = "slot"; CANARY = "canary"
    BLUE_GREEN = "blue_green"; STAMP = "stamp"

class RecoveryActionType(StrEnum):
    ROLLBACK = "rollback"; ROLL_FORWARD = "roll_forward"; FALLBACK = "fallback"

@dataclass(slots=True, frozen=True)
class RecoveryAction:
    action_type: RecoveryActionType
    target_revision_or_slot: str
    initiated_reason: str
    max_attempts: int = 2

def evaluate_exposure_step(current_percent, *, is_healthy, policy, step_size=25) -> tuple[int, RecoveryAction | None]:
    """Unhealthy -> roll back to 0% (if auto-rollback enabled) or hold at
    the current percent with a FALLBACK action. Healthy -> advance by
    step_size, capped at 100, with no action."""


class VerificationDimension(StrEnum):
    CONVERGENCE = "convergence"; HEALTH = "health"; SMOKE = "smoke"; BAKE_WINDOW = "bake_window"

@dataclass(slots=True, frozen=True)
class VerificationResult:
    passed: bool
    dimension_results: Mapping[str, bool]
    failed_dimension: VerificationDimension | None = None
    failure_reason: str | None = None

def evaluate_verification_contract(
    contract, *, convergence_succeeded, health_status_code, smoke_commands_passed, bake_window_errors_count,
) -> VerificationResult:
    """Checks all 4 dimensions in order — convergence, then a 2xx health
    status, then smoke tests, then a zero-error bake window — and fails
    fast on the first one that doesn't pass."""
```

---

## 21. Errors

```python
class VibeyError(Exception): ...
class InvalidPhaseError(VibeyError): ...
class IllegalTransitionError(VibeyError): ...
class NoEligibleEngine(VibeyError): ...
class EscalationExhausted(VibeyError):
    def __init__(self, attempt: int) -> None: ...
class HandoffRejected(VibeyError):
    def __init__(self, result: GateResult) -> None: ...
class InvalidSpecError(VibeyError): ...
class BudgetExceeded(VibeyError): ...
class UnknownProject(VibeyError):
    """No project exists with the given id."""
class WrongPhase(VibeyError):
    """The project is not in a phase the requested command applies to."""
class InvalidAnswer(VibeyError):
    """A human-gate answer was not in the expected QUESTION_ID=ANSWER form."""
class UnknownProvider(VibeyError):
    """The requested engine provider is not one vibey knows how to build."""
```

---

## 22. What must never appear in `domain/`

Checked by `import-linter` and by a test that walks the AST:

- `import asyncio`, `async def`, `await`
- `open()`, `pathlib`, `subprocess`, `os.environ`
- `asyncpg`, `psycopg`, `httpx`, `typer`, `structlog`, `pydantic`
- `datetime.now()` — time is always a parameter, never ambient

That last one is why every function here takes `now: datetime`. It is what makes
the wait-policy and circuit-breaker tests deterministic instead of flaky.

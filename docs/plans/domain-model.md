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
    INTAKE = "intake"; DESIGN = "design"; BUILD = "build"
    REVIEW = "review"; DEPLOY_DESIGN = "deploy_design"
    DEPLOY_EXECUTE = "deploy_execute"; DEPLOY_REVIEW = "deploy_review"
    DONE = "done"; ABANDONED = "abandoned"

TERMINAL: frozenset[Phase] = frozenset({Phase.DONE, Phase.ABANDONED})
INTERACTIVE: frozenset[Phase] = frozenset({
    Phase.DESIGN, Phase.REVIEW, Phase.DEPLOY_DESIGN, Phase.DEPLOY_REVIEW,
})


@dataclass(frozen=True, slots=True)
class PhaseState:
    phase: Phase
    cycle: int
    max_cycles: int
    entered_at: datetime

    def __post_init__(self) -> None:
        if self.cycle < 1:
            raise InvalidPhaseError("cycle must be >= 1")


@dataclass(frozen=True, slots=True)
class TransitionRequest:
    to: Phase
    reason: str
    evidence: TransitionEvidence


@dataclass(frozen=True, slots=True)
class TransitionEvidence:
    """Everything a guard needs. Assembled by application/, evaluated here."""
    acceptance_criteria: int = 0
    open_blocking_questions: int = 0
    unmapped_criteria: tuple[str, ...] = ()
    work_items_total: int = 0
    work_items_settled: int = 0          # integrated | waived
    integration_green: bool = False
    open_findings: tuple[FindingRef, ...] = ()
    user_verdict: UserVerdict | None = None
    budget_exhausted: bool = False
    blocked_on_ambiguity: int = 0
    deployment_spec_complete: bool = False
    deployment_consent_recorded: bool = False
    preflight_accepted: bool = False
    deployment_outcome: DeploymentOutcome | None = None
    deployment_attempt: int = 0
    deployment_attempt_cap: int = 0


Allowed = Literal["allowed"]

@dataclass(frozen=True, slots=True)
class Denied:
    violations: tuple[str, ...]

TransitionOutcome = Allowed | Denied


def evaluate_transition(
    state: PhaseState, request: TransitionRequest
) -> TransitionOutcome: ...


def next_phase_after_review(
    findings: Sequence[FindingRef], *, strict_loopback: bool
) -> Phase:
    """The routing decision from ADR-0010, isolated so it is trivially testable."""
    if not findings:
        return Phase.DEPLOY_DESIGN
    if strict_loopback:
        return Phase.DESIGN
    if any(f.ambiguity is Ambiguity.NEEDS_CLARIFICATION for f in findings):
        return Phase.DESIGN
    return Phase.BUILD


def next_phase_after_deploy_review(
    outcome: DeploymentOutcome, verdict: DeploymentVerdict
) -> Phase:
    """Route success, deployment-input changes, retries, and product defects."""
    ...
```

### Invariants (property-tested)

- Every non-terminal phase reaches `DONE` by some path from `INTAKE`.
- `DONE` and `ABANDONED` have no outgoing edges.
- No transition is legal when `cycle > max_cycles` except `→ ABANDONED`.
- `DEPLOY_EXECUTE → DEPLOY_EXECUTE` is illegal at the attempt/time/cost cap.
- No incomplete, unconsented deployment specification reaches `DEPLOY_EXECUTE`.
- `evaluate_transition` is total: every `(state, request)` pair returns without raising.

---

## 3. `effort.py`

```python
class Effort(IntEnum):
    TRIVIAL = 0; LOW = 1; STANDARD = 2; HIGH = 3; MAX = 4


PHASE_BASE_EFFORT: Mapping[Phase, Effort] = {
    Phase.DESIGN: Effort.HIGH,     # the user's requirement
    Phase.BUILD:  Effort.LOW,      # the user's requirement
    Phase.REVIEW: Effort.HIGH,     # the user's requirement
    Phase.DEPLOY_DESIGN: Effort.HIGH,
    Phase.DEPLOY_EXECUTE: Effort.LOW,
    Phase.DEPLOY_REVIEW: Effort.HIGH,
}

# attempt -> effort, for Phase 2's per-item escalation ladder
BUILD_LADDER: tuple[Effort, ...] = (
    Effort.LOW, Effort.LOW,
    Effort.STANDARD, Effort.STANDARD,
    Effort.HIGH, Effort.HIGH,
)
BUILD_LADDER_EXHAUSTED = len(BUILD_LADDER)   # attempt 7 → human gate


def effort_for_attempt(base: Effort, attempt: int) -> Effort:
    """Phase 2 escalation. Never lowers below base; saturates at HIGH."""
    if attempt <= 0:
        raise ValueError("attempt is 1-based")
    if attempt > BUILD_LADDER_EXHAUSTED:
        raise EscalationExhausted(attempt)
    return max(base, BUILD_LADDER[attempt - 1])


def forces_rotation(previous: Effort, current: Effort) -> bool:
    return current > previous
```

---

## 4. `engine.py`

```python
class EngineId(StrEnum):
    CLAUDELOOP = "claudeloop"; CODEXLOOP = "codexloop"
    CURSORLOOP = "cursorloop"; AGYLOOP = "agyloop"


class Capability(StrEnum):
    SAVEPOINTS = "savepoints"; UNWIND = "unwind"
    STRUCTURED_VERDICT = "structured_verdict"
    MID_RUN_PROMPT = "mid_run_prompt"; MID_RUN_MODEL = "mid_run_model"
    MID_RUN_EFFORT = "mid_run_effort"; ATTACHMENTS = "attachments"
    SLASH_COMMANDS = "slash_commands"; WEB_SEARCH = "web_search"
    SNAPSHOT = "snapshot"; SANDBOX = "sandbox"


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

    def invoke(self, effort: Effort) -> EngineInvocation: ...

    def saturates_at(self, effort: Effort) -> bool:
        return self.invoke(effort).achieved < effort


@dataclass(frozen=True, slots=True)
class JobRequirement:
    effort: Effort
    capabilities: frozenset[Capability] = frozenset()
    excluded: frozenset[EngineId] = frozenset()   # the "must differ" constraint
```

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
    a BackoffProbe, never a DeadlineProbe — because there is no deadline."""
    match capacity:
        case Available():
            return None
        case WindowExhausted(resets_at=dt) if dt is not None:
            return DeadlineProbe(at=dt + _jitter())
        case WindowExhausted():
            return BackoffProbe(next_at=now + _backoff(attempt, cap=timedelta(minutes=5)),
                                attempt=attempt)
        case CreditsExhausted():
            return BackoffProbe(next_at=now + _backoff(attempt, floor=timedelta(minutes=5),
                                                       cap=timedelta(minutes=30)),
                                attempt=attempt)
        case AuthenticationFailed():
            return None          # waiting cannot fix credentials
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
        return max(0, round(self.base_weight * self.health_factor
                            * self.fidelity_factor * self.cost_factor
                            * self.affinity_factor))


@dataclass(frozen=True, slots=True)
class Selection:
    engine_id: EngineId
    achieved_effort: Effort
    saturated: bool
    candidates: tuple[Candidate, ...]     # updated SWRR state


def eligible(runtimes, *, requirement, phase, allow_list, now) -> tuple[EngineRuntime, ...]: ...
def select(candidates: Sequence[Candidate]) -> Selection: ...      # smooth WRR
def health_factor(circuit: Circuit) -> float: ...
def fidelity_factor(descriptor: EngineDescriptor, requested: Effort) -> float: ...
def cost_factor(descriptor, *, median_cost: float, enabled: bool) -> float: ...
def affinity_factor(*, holds_warm_session: bool, rotation_forced: bool) -> float: ...
```

### Properties

| Property | Statement |
|---|---|
| **No starvation** | Over `sum(effective_weight)` consecutive selections, every candidate with `effective_weight > 0` is selected at least once |
| **Weight fidelity** | Selection counts converge to weight ratios within ±1 over any full period |
| **Smoothness** | No candidate is selected twice consecutively while another with `effective_weight > 0` has gone unselected longer |
| **Determinism** | Identical candidate state produces an identical selection |
| **Totality** | `select` raises `NoEligibleEngine` iff every `effective_weight` is 0 |
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
    """Ids opened by `kind` and not yet closed or superseded. The gate's primitive."""
```

---

## 9. `handoff.py` and `noloss.py`

Specified in full in [handoff-protocol.md](handoff-protocol.md). The domain types:

```python
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


def verify(*, ledger, brief, ref, budget, spec_constraints, mode=GateMode.STRICT) -> GateResult:
    """Pure. No model call. This function is the reason rotation is safe."""
```

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
def idempotency_key(project_id, cycle, kind, subject) -> str: ...


# spec.py
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


# review.py
class Severity(StrEnum): CRITICAL="critical"; HIGH="high"; MEDIUM="medium"; LOW="low"
class Ambiguity(StrEnum): CLEAR="clear"; NEEDS_CLARIFICATION="needs_clarification"
class UserVerdict(StrEnum): ACCEPT="accept"; CHANGES="changes"; CANCEL="cancel"


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

## 11. Errors

```python
class VibeyError(Exception): ...
class InvalidPhaseError(VibeyError): ...
class IllegalTransitionError(VibeyError): ...
class NoEligibleEngine(VibeyError): ...
class EscalationExhausted(VibeyError): ...
class HandoffRejected(VibeyError):
    def __init__(self, result: GateResult) -> None: ...
class InvalidSpecError(VibeyError): ...
class BudgetExceeded(VibeyError): ...
```

---

## 12. What must never appear in `domain/`

Checked by `import-linter` and by a test that walks the AST:

- `import asyncio`, `async def`, `await`
- `open()`, `pathlib`, `subprocess`, `os.environ`
- `asyncpg`, `psycopg`, `httpx`, `typer`, `structlog`, `pydantic`
- `datetime.now()` — time is always a parameter, never ambient

That last one is why every function here takes `now: datetime`. It is what makes
the wait-policy and circuit-breaker tests deterministic instead of flaky.

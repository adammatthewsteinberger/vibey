# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The no-loss gate: a pure predicate that a handoff brief has not dropped
anything the ledger says is still open (ADR-0004). No I/O, no model call."""

from collections.abc import Sequence

from vibey.domain.handoff import (
    BudgetSnapshot,
    GateMode,
    GateResult,
    GateRule,
    HandoffBrief,
    LedgerRef,
    Violation,
)
from vibey.domain.ledger import EventKind, LedgerEvent, digest_range, open_items

# Substrings that, if present in a brief's free-text fields, indicate an
# attempted injection: a tool grant, a permission change, or an
# acceptance-criteria mutation smuggled through the brief. R10 is the
# security control from the architecture threat model.
_CONTAINMENT_DENYLIST = (
    "grant tool",
    "grant permission",
    "change acceptance criteria",
    "modify acceptance criteria",
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard the spec",
    "you now have permission",
    "sudo",
)


def _as_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    raise TypeError(f"expected a number, got {type(value).__name__}")


def _as_int(value: object) -> int:
    if isinstance(value, int):
        return value
    raise TypeError(f"expected an int, got {type(value).__name__}")


def _brief_text_fields(brief: HandoffBrief) -> tuple[str, ...]:
    return (
        brief.objective,
        brief.next_action,
        *brief.constraints,
        *brief.done,
        *brief.invariants,
        *brief.style_rules,
        *(r.text for r in brief.remaining),
        *(d.restatement for d in brief.decisions),
        *(a.restatement for a in brief.assumptions),
        *(q.text for q in brief.open_questions),
    )


def _check_r1_remaining(
    ledger: Sequence[LedgerEvent], brief: HandoffBrief
) -> tuple[Violation, ...]:
    latest_verdict = None
    for event in sorted(ledger, key=lambda e: e.seq):
        if event.kind is EventKind.VERDICT_RENDERED:
            latest_verdict = event

    if latest_verdict is None:
        return ()

    remaining_work_raw = latest_verdict.payload.get("remaining_work", [])
    remaining_work = remaining_work_raw if isinstance(remaining_work_raw, list) else []
    brief_texts = {r.text for r in brief.remaining}

    violations = []
    for item in remaining_work:
        text = str(item)
        if text not in brief_texts:
            violations.append(
                Violation(
                    rule=GateRule.R1_REMAINING,
                    item_id=None,
                    detail=f"missing remaining item: {text!r}",
                )
            )
    return tuple(violations)


def _check_r2_questions(
    ledger: Sequence[LedgerEvent], brief: HandoffBrief
) -> tuple[Violation, ...]:
    open_ids = set(open_items(ledger, EventKind.QUESTION_ASKED))
    brief_ids = {q.question_id for q in brief.open_questions}
    missing = open_ids - brief_ids
    return tuple(
        Violation(
            rule=GateRule.R2_QUESTIONS,
            item_id=qid,
            detail=f"open question {qid!r} missing from brief",
        )
        for qid in sorted(missing)
    )


def _check_r3_decisions(
    ledger: Sequence[LedgerEvent], brief: HandoffBrief
) -> tuple[Violation, ...]:
    open_ids = set(open_items(ledger, EventKind.DECISION_RECORDED))
    brief_ids = {d.decision_id for d in brief.decisions}
    missing = open_ids - brief_ids
    return tuple(
        Violation(
            rule=GateRule.R3_DECISIONS, item_id=did, detail=f"decision {did!r} missing from brief"
        )
        for did in sorted(missing)
    )


def _check_r4_assumptions(
    ledger: Sequence[LedgerEvent], brief: HandoffBrief
) -> tuple[Violation, ...]:
    open_ids = set(open_items(ledger, EventKind.ASSUMPTION_STATED))
    brief_ids = {a.assumption_id for a in brief.assumptions}
    missing = open_ids - brief_ids
    return tuple(
        Violation(
            rule=GateRule.R4_ASSUMPTIONS,
            item_id=aid,
            detail=f"assumption {aid!r} missing from brief",
        )
        for aid in sorted(missing)
    )


def _check_r5_findings(ledger: Sequence[LedgerEvent], brief: HandoffBrief) -> tuple[Violation, ...]:
    open_ids = set(open_items(ledger, EventKind.FINDING_RAISED))
    brief_ids = {f.finding_id for f in brief.open_findings}
    missing = open_ids - brief_ids
    return tuple(
        Violation(
            rule=GateRule.R5_FINDINGS, item_id=fid, detail=f"finding {fid!r} missing from brief"
        )
        for fid in sorted(missing)
    )


def _check_r6_range(ledger: Sequence[LedgerEvent], ref: LedgerRef) -> tuple[Violation, ...]:
    violations = []
    if ref.digest != digest_range(ledger):
        violations.append(
            Violation(rule=GateRule.R6_RANGE, item_id=None, detail="range digest mismatch")
        )
    if ref.event_count != len(ledger):
        violations.append(
            Violation(
                rule=GateRule.R6_RANGE,
                item_id=None,
                detail="event_count does not match ledger length",
            )
        )
    max_seq = max((e.seq for e in ledger), default=None)
    if max_seq is not None and ref.to_seq != max_seq:
        violations.append(
            Violation(
                rule=GateRule.R6_RANGE,
                item_id=None,
                detail="to_seq does not match max(seq) in range",
            )
        )
    return tuple(violations)


def _check_r7_artifacts(
    ledger: Sequence[LedgerEvent], brief: HandoffBrief
) -> tuple[Violation, ...]:
    referenced_ids = {
        str(e.payload["artifact_id"])
        for e in ledger
        if e.kind is EventKind.ARTIFACT_PRODUCED and e.payload.get("referenced_by_open_item")
    }
    brief_ids = {a.artifact_id for a in brief.artifacts}
    missing = referenced_ids - brief_ids
    return tuple(
        Violation(
            rule=GateRule.R7_ARTIFACTS, item_id=aid, detail=f"artifact {aid!r} missing from brief"
        )
        for aid in sorted(missing)
    )


def _check_r8_budget(
    ledger: Sequence[LedgerEvent], budget: BudgetSnapshot
) -> tuple[Violation, ...]:
    spend_events = [e for e in ledger if e.kind is EventKind.BUDGET_SPENT]
    spent_dollars = sum(_as_float(e.payload.get("dollars", 0.0)) for e in spend_events)
    spent_turns = sum(_as_int(e.payload.get("turns", 0)) for e in spend_events)
    violations = []
    if abs(spent_dollars - budget.dollars_spent) > 1e-9:
        violations.append(
            Violation(
                rule=GateRule.R8_BUDGET,
                item_id=None,
                detail=(
                    f"budget.dollars_spent={budget.dollars_spent} but "
                    f"ledger sums to {spent_dollars}"
                ),
            )
        )
    if spent_turns != budget.turns_spent:
        violations.append(
            Violation(
                rule=GateRule.R8_BUDGET,
                item_id=None,
                detail=f"budget.turns_spent={budget.turns_spent} but ledger sums to {spent_turns}",
            )
        )
    return tuple(violations)


def _check_r9_constraints(
    brief: HandoffBrief, spec_constraints: Sequence[str]
) -> tuple[Violation, ...]:
    missing = set(spec_constraints) - set(brief.constraints)
    return tuple(
        Violation(
            rule=GateRule.R9_CONSTRAINTS, item_id=None, detail=f"hard constraint missing: {c!r}"
        )
        for c in sorted(missing)
    )


def _check_r10_containment(brief: HandoffBrief) -> tuple[Violation, ...]:
    violations = []
    for text in _brief_text_fields(brief):
        lowered = text.lower()
        for pattern in _CONTAINMENT_DENYLIST:
            if pattern in lowered:
                violations.append(
                    Violation(
                        rule=GateRule.R10_CONTAINMENT,
                        item_id=None,
                        detail=f"suspicious phrase {pattern!r} found in brief text",
                    )
                )
    return tuple(violations)


# Rules auto-satisfied by construction under FULL_TRANSCRIPT mode: the whole
# ledger range is inlined into the prompt, so closure over the brief alone is
# no longer meaningful. R6, R8, and R10 still run because they check facts
# about the range and the brief's containment, not brief completeness.
_AUTO_SATISFIED_UNDER_FULL_TRANSCRIPT = frozenset(
    {
        GateRule.R1_REMAINING,
        GateRule.R2_QUESTIONS,
        GateRule.R3_DECISIONS,
        GateRule.R4_ASSUMPTIONS,
        GateRule.R5_FINDINGS,
        GateRule.R7_ARTIFACTS,
        GateRule.R9_CONSTRAINTS,
    }
)


def verify(
    *,
    ledger: Sequence[LedgerEvent],
    brief: HandoffBrief,
    ref: LedgerRef,
    budget: BudgetSnapshot,
    spec_constraints: Sequence[str] = (),
    mode: GateMode = GateMode.STRICT,
    attempts: int = 1,
) -> GateResult:
    """Pure. No model call. This function is the reason rotation is safe."""
    checks: dict[GateRule, tuple[Violation, ...]] = {
        GateRule.R1_REMAINING: _check_r1_remaining(ledger, brief),
        GateRule.R2_QUESTIONS: _check_r2_questions(ledger, brief),
        GateRule.R3_DECISIONS: _check_r3_decisions(ledger, brief),
        GateRule.R4_ASSUMPTIONS: _check_r4_assumptions(ledger, brief),
        GateRule.R5_FINDINGS: _check_r5_findings(ledger, brief),
        GateRule.R6_RANGE: _check_r6_range(ledger, ref),
        GateRule.R7_ARTIFACTS: _check_r7_artifacts(ledger, brief),
        GateRule.R8_BUDGET: _check_r8_budget(ledger, budget),
        GateRule.R9_CONSTRAINTS: _check_r9_constraints(brief, spec_constraints),
        GateRule.R10_CONTAINMENT: _check_r10_containment(brief),
    }

    if mode is GateMode.FULL_TRANSCRIPT:
        for rule in _AUTO_SATISFIED_UNDER_FULL_TRANSCRIPT:
            checks[rule] = ()

    rules_run = tuple(GateRule)
    violations = tuple(v for rule in rules_run for v in checks[rule])

    return GateResult(
        ok=not violations,
        mode=mode,
        attempts=attempts,
        violations=violations,
        rules_run=rules_run,
    )

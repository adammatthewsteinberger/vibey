"""Pure projections over a replayed event range (architecture-and-roadmap.md
§4): OpenItems, DecisionLog, and CostReport. Projections are derived and
disposable -- any of them can be rebuilt by replaying the log, which is
exactly what makes them safe to materialize for query speed without ever
becoming a second source of truth."""

from collections.abc import Sequence
from dataclasses import dataclass

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, LedgerEvent, open_items
from vibey.domain.phase import Phase


@dataclass(frozen=True, slots=True)
class OpenItemsView:
    questions: tuple[str, ...]
    decisions: tuple[str, ...]
    assumptions: tuple[str, ...]
    findings: tuple[str, ...]


def build_open_items(events: Sequence[LedgerEvent]) -> OpenItemsView:
    return OpenItemsView(
        questions=open_items(events, EventKind.QUESTION_ASKED),
        decisions=open_items(events, EventKind.DECISION_RECORDED),
        assumptions=open_items(events, EventKind.ASSUMPTION_STATED),
        findings=open_items(events, EventKind.FINDING_RAISED),
    )


@dataclass(frozen=True, slots=True)
class DecisionLogEntry:
    """ADR-shaped: every decision ever recorded, open or superseded."""

    decision_id: str
    title: str
    choice: str
    rationale: str
    alternatives: tuple[str, ...]
    superseded_by: str | None
    seq: int


def build_decision_log(events: Sequence[LedgerEvent]) -> tuple[DecisionLogEntry, ...]:
    superseded_by: dict[str, str] = {}
    entries: dict[str, DecisionLogEntry] = {}

    for event in sorted(events, key=lambda e: e.seq):
        if event.kind is not EventKind.DECISION_RECORDED:
            continue
        decision_id = str(event.payload["decision_id"])
        supersedes = event.payload.get("supersedes")
        if supersedes is not None:
            superseded_by[str(supersedes)] = decision_id
        entries[decision_id] = DecisionLogEntry(
            decision_id=decision_id,
            title=str(event.payload.get("title", "")),
            choice=str(event.payload.get("choice", "")),
            rationale=str(event.payload.get("rationale", "")),
            alternatives=_as_str_tuple(event.payload.get("alternatives", [])),
            superseded_by=None,
            seq=event.seq,
        )

    return tuple(
        DecisionLogEntry(
            decision_id=e.decision_id,
            title=e.title,
            choice=e.choice,
            rationale=e.rationale,
            alternatives=e.alternatives,
            superseded_by=superseded_by.get(e.decision_id),
            seq=e.seq,
        )
        for e in sorted(entries.values(), key=lambda e: e.seq)
    )


@dataclass(frozen=True, slots=True)
class CostReportEntry:
    phase: Phase
    engine_id: EngineId | None
    turns: int
    dollars: float


def build_cost_report(events: Sequence[LedgerEvent]) -> tuple[CostReportEntry, ...]:
    totals: dict[tuple[Phase, EngineId | None], list[float]] = {}

    for event in events:
        if event.kind is not EventKind.BUDGET_SPENT:
            continue
        key = (event.phase, event.engine_id)
        turns, dollars = totals.setdefault(key, [0, 0.0])
        turns_val = event.payload.get("turns", 0)
        dollars_val = event.payload.get("dollars", 0.0)
        totals[key][0] = turns + (turns_val if isinstance(turns_val, int | float) else 0)
        totals[key][1] = dollars + (dollars_val if isinstance(dollars_val, int | float) else 0.0)

    return tuple(
        CostReportEntry(phase=phase, engine_id=engine_id, turns=int(t), dollars=d)
        for (phase, engine_id), (t, d) in sorted(
            totals.items(), key=lambda kv: (kv[0][0].value, str(kv[0][1]))
        )
    )


@dataclass(frozen=True, slots=True)
class WorkLedgerEntry:
    """Per work-thread status, keyed by correlation_id -- the closest thing
    the event log has to a stable work-item identifier. This is a narrower
    projection than the full work_item table (which additionally tracks
    branch/worktree/verification state outside the ledger's vocabulary);
    it answers "is this thread of work done, and what's left" from replay
    alone."""

    correlation_id: str
    complete: bool
    remaining_work: tuple[str, ...]
    last_seq: int


def build_work_ledger(events: Sequence[LedgerEvent]) -> tuple[WorkLedgerEntry, ...]:
    latest: dict[str, LedgerEvent] = {}
    for event in sorted(events, key=lambda e: e.seq):
        if event.kind is not EventKind.VERDICT_RENDERED:
            continue
        latest[str(event.correlation_id)] = event

    return tuple(
        WorkLedgerEntry(
            correlation_id=cid,
            complete=bool(event.payload.get("complete", False)),
            remaining_work=_as_str_tuple(event.payload.get("remaining_work", [])),
            last_seq=event.seq,
        )
        for cid, event in sorted(latest.items(), key=lambda kv: kv[1].seq)
    )


def _as_str_tuple(value: object) -> tuple[str, ...]:
    return tuple(str(v) for v in value) if isinstance(value, list) else ()

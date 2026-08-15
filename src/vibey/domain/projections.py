"""Pure projections over a replayed event range (architecture-and-roadmap.md
§4): OpenItems, DecisionLog, CostReport, Deltas, and Q&A. Projections are derived and
disposable -- any of them can be rebuilt by replaying the log, which is
exactly what makes them safe to materialize for query speed without ever
becoming a second source of truth."""

from collections.abc import Sequence
from dataclasses import dataclass

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, LedgerEvent, open_items
from vibey.domain.phase import Phase
from vibey.domain.review import (
    Ambiguity,
    AssumptionDelta,
    DeltasReport,
    FindingDelta,
    Severity,
)


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


def build_deltas(events: Sequence[LedgerEvent]) -> DeltasReport:
    """Builds a DeltasReport from ledger events.

    Assumptions and findings cannot be silently omitted from the review:
    every AssumptionStated and FindingRaised event recorded during the run
    is surfaced here.
    """
    assumptions_map: dict[str, AssumptionDelta] = {}
    findings_map: dict[str, FindingDelta] = {}
    resolved_findings: set[str] = set()

    for event in sorted(events, key=lambda e: e.seq):
        if event.kind is EventKind.ASSUMPTION_STATED:
            aid = str(event.payload.get("assumption_id", ""))
            text = str(event.payload.get("text", ""))
            if aid:
                assumptions_map[aid] = AssumptionDelta(assumption_id=aid, text=text, seq=event.seq)
        elif event.kind is EventKind.FINDING_RAISED:
            fid = str(event.payload.get("finding_id", ""))
            sev_str = str(event.payload.get("severity", "low")).lower()
            amb_str = str(event.payload.get("ambiguity", "needs_clarification")).lower()
            text = str(event.payload.get("text", ""))
            try:
                severity = Severity(sev_str)
            except ValueError:
                severity = Severity.LOW
            try:
                ambiguity = Ambiguity(amb_str)
            except ValueError:
                ambiguity = Ambiguity.NEEDS_CLARIFICATION
            if fid:
                findings_map[fid] = FindingDelta(
                    finding_id=fid,
                    severity=severity,
                    ambiguity=ambiguity,
                    text=text,
                    seq=event.seq,
                    resolved=fid in resolved_findings,
                )
        elif event.kind is EventKind.FINDING_RESOLVED:
            fid = str(event.payload.get("finding_id", ""))
            if fid:
                resolved_findings.add(fid)
                if fid in findings_map:
                    prior = findings_map[fid]
                    findings_map[fid] = FindingDelta(
                        finding_id=prior.finding_id,
                        severity=prior.severity,
                        ambiguity=prior.ambiguity,
                        text=prior.text,
                        seq=prior.seq,
                        resolved=True,
                    )

    return DeltasReport(
        assumptions=tuple(sorted(assumptions_map.values(), key=lambda a: a.seq)),
        findings=tuple(sorted(findings_map.values(), key=lambda f: f.seq)),
    )


_STOPWORDS = frozenset(
    {
        "why",
        "did",
        "you",
        "use",
        "the",
        "for",
        "what",
        "how",
        "and",
        "with",
        "from",
        "is",
        "a",
        "an",
    }
)


def answer_why_question(events: Sequence[LedgerEvent], question: str) -> str:
    """Answers developer questions about what was built by reading the ledger.

    Examines DecisionRecorded and AssumptionStated events so that answers explain
    the recorded rationale rather than inventing a new one from a fresh model call.
    """
    words = [
        w.strip("?,.!:;\"'")
        for w in question.lower().split()
        if w.strip("?,.!:;\"'") not in _STOPWORDS and len(w.strip("?,.!:;\"'")) > 1
    ]

    decisions: list[dict[str, object]] = []
    assumptions: list[dict[str, object]] = []

    for e in events:
        if e.kind is EventKind.DECISION_RECORDED:
            decisions.append(dict(e.payload))
        elif e.kind is EventKind.ASSUMPTION_STATED:
            assumptions.append(dict(e.payload))

    matched_decisions = []
    for d in decisions:
        alts = " ".join(_as_str_tuple(d.get("alternatives", [])))
        combined = (
            f"{d.get('decision_id', '')} {d.get('title', '')} "
            f"{d.get('choice', '')} {d.get('rationale', '')} {alts}"
        ).lower()
        if any(w in combined for w in words):
            matched_decisions.append(d)

    matched_assumptions = []
    for a in assumptions:
        combined = f"{a.get('assumption_id', '')} {a.get('text', '')}".lower()
        if any(w in combined for w in words):
            matched_assumptions.append(a)

    target_decisions = matched_decisions if matched_decisions else decisions
    target_assumptions = matched_assumptions if matched_assumptions else assumptions

    if not target_decisions and not target_assumptions:
        return "No decisions or assumptions recorded in the ledger."

    lines: list[str] = ["Based on the ledger:"]
    for d in target_decisions:
        did = d.get("decision_id", "decision")
        title = d.get("title", "")
        choice = d.get("choice", "")
        rationale = d.get("rationale", "")
        lines.append(f"- Decision [{did}] '{title}': chose '{choice}' because {rationale}")
    for a in target_assumptions:
        aid = a.get("assumption_id", "assumption")
        text = a.get("text", "")
        lines.append(f"- Assumption [{aid}]: {text}")

    return "\n".join(lines)


def _as_str_tuple(value: object) -> tuple[str, ...]:
    return tuple(str(v) for v in value) if isinstance(value, list) else ()

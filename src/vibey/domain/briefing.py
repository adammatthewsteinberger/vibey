# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The deterministic template brief: vibey's own floor producer
(handoff-protocol.md §6.5, option 4). Built directly from the same
projections domain/noloss.py's gate checks, so it always passes the gate
by construction -- no model call, less fluent than an LLM-written brief,
but never lossy. This is what makes "all engines are down" a
degraded-quality scenario rather than a data-loss one."""

from collections.abc import Sequence

from vibey.domain.handoff import (
    ArtifactRef,
    AssumptionRef,
    DecisionRef,
    HandoffBrief,
    QuestionRef,
    RemainingItem,
)
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.projections import build_decision_log, build_open_items
from vibey.domain.review import Ambiguity, FindingRef, Severity


def _latest_verdict(events: Sequence[LedgerEvent]) -> LedgerEvent | None:
    latest: LedgerEvent | None = None
    for event in sorted(events, key=lambda e: e.seq):
        if event.kind is EventKind.VERDICT_RENDERED:
            latest = event
    return latest


def build_deterministic_brief(
    events: Sequence[LedgerEvent],
    *,
    objective: str = "See the accepted spec in .vibey/context/spec.md.",
    spec_constraints: Sequence[str] = (),
    invariants: Sequence[str] = (),
    style_rules: Sequence[str] = (),
) -> HandoffBrief:
    open_view = build_open_items(events)
    decision_log = build_decision_log(events)

    question_text: dict[str, str] = {}
    question_blocking: dict[str, bool] = {}
    for event in events:
        if event.kind is EventKind.QUESTION_ASKED:
            qid = str(event.payload["question_id"])
            question_text[qid] = str(event.payload.get("text", ""))
            question_blocking[qid] = bool(event.payload.get("blocking", False))

    assumption_text: dict[str, str] = {}
    for event in events:
        if event.kind is EventKind.ASSUMPTION_STATED:
            aid = str(event.payload["assumption_id"])
            assumption_text[aid] = str(event.payload.get("text", ""))

    finding_meta: dict[str, tuple[Severity, Ambiguity]] = {}
    for event in events:
        if event.kind is EventKind.FINDING_RAISED:
            fid = str(event.payload["finding_id"])
            severity_raw = str(event.payload.get("severity", "low"))
            ambiguity_raw = str(event.payload.get("ambiguity", "clear"))
            try:
                severity = Severity(severity_raw)
            except ValueError:
                severity = Severity.LOW
            try:
                ambiguity = Ambiguity(ambiguity_raw)
            except ValueError:
                ambiguity = Ambiguity.CLEAR
            finding_meta[fid] = (severity, ambiguity)

    referenced_artifacts: dict[str, str] = {}
    for event in events:
        if event.kind is EventKind.ARTIFACT_PRODUCED and event.payload.get(
            "referenced_by_open_item"
        ):
            aid = str(event.payload["artifact_id"])
            referenced_artifacts[aid] = str(event.payload.get("path", ""))

    verdict = _latest_verdict(events)
    remaining_raw = verdict.payload.get("remaining_work", []) if verdict is not None else []
    remaining_texts = [str(t) for t in remaining_raw] if isinstance(remaining_raw, list) else []

    decisions = tuple(
        DecisionRef(decision_id=e.decision_id, restatement=e.title or e.choice)
        for e in decision_log
        if e.superseded_by is None
    )

    next_action = remaining_texts[0] if remaining_texts else "Review and accept."

    return HandoffBrief(
        objective=objective,
        constraints=tuple(spec_constraints),
        decisions=decisions,
        assumptions=tuple(
            AssumptionRef(assumption_id=aid, restatement=assumption_text.get(aid, ""))
            for aid in open_view.assumptions
        ),
        done=(),
        remaining=tuple(RemainingItem(text=t) for t in remaining_texts),
        open_questions=tuple(
            QuestionRef(
                question_id=qid,
                text=question_text.get(qid, ""),
                blocking=question_blocking.get(qid, False),
            )
            for qid in open_view.questions
        ),
        open_findings=tuple(
            FindingRef(
                finding_id=fid, severity=finding_meta[fid][0], ambiguity=finding_meta[fid][1]
            )
            for fid in open_view.findings
        ),
        artifacts=tuple(
            ArtifactRef(artifact_id=aid, path=path) for aid, path in referenced_artifacts.items()
        ),
        invariants=tuple(invariants),
        style_rules=tuple(style_rules),
        next_action=next_action,
    )

from datetime import UTC, datetime
from uuid import uuid4

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event
from vibey.domain.phase import Phase
from vibey.domain.projections import (
    answer_why_question,
    build_cost_report,
    build_decision_log,
    build_deltas,
    build_open_items,
    build_work_ledger,
)

PROJECT_ID = uuid4()
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _event(
    seq: int,
    kind: EventKind,
    payload: dict[str, object],
    *,
    phase: Phase = Phase.BUILD,
    engine_id: EngineId | None = None,
    correlation_id: object | None = None,
) -> LedgerEvent:
    return LedgerEvent(
        event_id=uuid4(),
        project_id=PROJECT_ID,
        cycle=1,
        phase=phase,
        seq=seq,
        kind=kind,
        engine_id=engine_id,
        job_id=None,
        causation_id=None,
        correlation_id=correlation_id or uuid4(),
        provenance=Provenance.AGENT,
        produced_at=NOW,
        payload=payload,
        digest=digest_event(payload),
    )


def test_build_open_items_reflects_open_items_across_all_kinds() -> None:
    events = [
        _event(1, EventKind.QUESTION_ASKED, {"question_id": "q1", "text": "?", "blocking": False}),
        _event(2, EventKind.DECISION_RECORDED, {"decision_id": "d1", "title": "t", "choice": "c"}),
        _event(
            3,
            EventKind.ASSUMPTION_STATED,
            {"assumption_id": "a1", "text": "x", "confidence": "high"},
        ),
        _event(4, EventKind.FINDING_RAISED, {"finding_id": "f1", "severity": "low", "text": "x"}),
    ]

    view = build_open_items(events)

    assert view.questions == ("q1",)
    assert view.decisions == ("d1",)
    assert view.assumptions == ("a1",)
    assert view.findings == ("f1",)


def test_build_open_items_empty_ledger() -> None:
    view = build_open_items([])
    assert view == build_open_items([])


def test_build_decision_log_includes_every_decision_ever_recorded() -> None:
    events = [
        _event(
            1,
            EventKind.DECISION_RECORDED,
            {
                "decision_id": "d1",
                "title": "Outbox over 2PC",
                "choice": "outbox",
                "rationale": "simpler",
                "alternatives": ["2PC"],
            },
        ),
        _event(
            2,
            EventKind.DECISION_RECORDED,
            {
                "decision_id": "d2",
                "title": "Postgres over Mongo",
                "choice": "postgres",
                "supersedes": "d1",
                "alternatives": [],
            },
        ),
    ]

    log = build_decision_log(events)

    assert len(log) == 2
    assert log[0].decision_id == "d1"
    assert log[1].decision_id == "d2"
    assert log[0].superseded_by == "d2"
    assert log[1].superseded_by is None
    assert log[0].alternatives == ("2PC",)


def test_build_decision_log_ignores_non_decision_events() -> None:
    events = [_event(1, EventKind.TURN_REQUESTED, {"prompt_digest": "x"})]
    assert build_decision_log(events) == ()


def test_build_cost_report_aggregates_by_phase_and_engine() -> None:
    events = [
        _event(
            1,
            EventKind.BUDGET_SPENT,
            {"dollars": 1.5, "turns": 2, "phase": "build"},
            phase=Phase.BUILD,
            engine_id=EngineId.CLAUDELOOP,
        ),
        _event(
            2,
            EventKind.BUDGET_SPENT,
            {"dollars": 2.5, "turns": 1, "phase": "build"},
            phase=Phase.BUILD,
            engine_id=EngineId.CLAUDELOOP,
        ),
        _event(
            3,
            EventKind.BUDGET_SPENT,
            {"dollars": 0.5, "turns": 1, "phase": "design"},
            phase=Phase.DESIGN,
            engine_id=EngineId.CODEXLOOP,
        ),
    ]

    report = build_cost_report(events)

    by_key = {(e.phase, e.engine_id): e for e in report}
    claudeloop_build = by_key[(Phase.BUILD, EngineId.CLAUDELOOP)]
    assert claudeloop_build.turns == 3
    assert claudeloop_build.dollars == 4.0

    codexloop_design = by_key[(Phase.DESIGN, EngineId.CODEXLOOP)]
    assert codexloop_design.turns == 1
    assert codexloop_design.dollars == 0.5


def test_build_cost_report_ignores_non_budget_events() -> None:
    events = [_event(1, EventKind.TURN_COMPLETED, {"cost_usd": 5.0})]
    assert build_cost_report(events) == ()


def test_build_cost_report_ignores_malformed_numeric_fields() -> None:
    events = [
        _event(
            1,
            EventKind.BUDGET_SPENT,
            {"dollars": "not-a-number", "turns": "also-not"},
            engine_id=EngineId.CLAUDELOOP,
        )
    ]
    report = build_cost_report(events)
    assert report[0].turns == 0
    assert report[0].dollars == 0.0


def test_build_work_ledger_uses_latest_verdict_per_correlation_id() -> None:
    cid = uuid4()
    events = [
        _event(
            1,
            EventKind.VERDICT_RENDERED,
            {"complete": False, "remaining_work": ["a"]},
            correlation_id=cid,
        ),
        _event(
            2,
            EventKind.VERDICT_RENDERED,
            {"complete": True, "remaining_work": []},
            correlation_id=cid,
        ),
    ]

    ledger = build_work_ledger(events)

    assert len(ledger) == 1
    assert ledger[0].complete is True
    assert ledger[0].remaining_work == ()
    assert ledger[0].last_seq == 2


def test_build_work_ledger_tracks_multiple_correlation_ids_independently() -> None:
    cid1, cid2 = uuid4(), uuid4()
    events = [
        _event(
            1,
            EventKind.VERDICT_RENDERED,
            {"complete": True, "remaining_work": []},
            correlation_id=cid1,
        ),
        _event(
            2,
            EventKind.VERDICT_RENDERED,
            {"complete": False, "remaining_work": ["x"]},
            correlation_id=cid2,
        ),
    ]

    ledger = build_work_ledger(events)

    assert {e.correlation_id for e in ledger} == {str(cid1), str(cid2)}


def test_build_work_ledger_ignores_non_verdict_events() -> None:
    events = [_event(1, EventKind.TURN_COMPLETED, {"cost_usd": 1.0})]
    assert build_work_ledger(events) == ()


def test_rebuild_from_replay_is_idempotent_and_deterministic() -> None:
    """'vibey ledger rebuild is a no-op on a healthy DB': replaying the same
    range twice through any projection produces identical output."""
    events = [
        _event(1, EventKind.QUESTION_ASKED, {"question_id": "q1", "text": "?", "blocking": False}),
        _event(
            2,
            EventKind.DECISION_RECORDED,
            {
                "decision_id": "d1",
                "title": "t",
                "choice": "c",
                "rationale": "r",
                "alternatives": [],
            },
        ),
        _event(
            3,
            EventKind.BUDGET_SPENT,
            {"dollars": 1.0, "turns": 1},
            engine_id=EngineId.CLAUDELOOP,
        ),
    ]

    assert build_open_items(events) == build_open_items(list(reversed(events)))
    assert build_decision_log(events) == build_decision_log(list(reversed(events)))
    assert build_cost_report(events) == build_cost_report(list(reversed(events)))
    assert build_work_ledger(events) == build_work_ledger(list(reversed(events)))


def test_build_deltas_ignores_assumptions_with_empty_id() -> None:
    """When assumption_id is empty, the assumption is not recorded."""
    events = [
        _event(1, EventKind.ASSUMPTION_STATED, {"assumption_id": "", "text": "ignored"}),
        _event(2, EventKind.ASSUMPTION_STATED, {"assumption_id": "a1", "text": "recorded"}),
    ]

    deltas = build_deltas(events)

    assert len(deltas.assumptions) == 1
    assert deltas.assumptions[0].assumption_id == "a1"


def test_build_deltas_ignores_findings_with_empty_id() -> None:
    """When finding_id is empty, the finding is not recorded."""
    events = [
        _event(1, EventKind.FINDING_RAISED, {"finding_id": "", "text": "ignored"}),
        _event(2, EventKind.FINDING_RAISED, {"finding_id": "f1", "text": "recorded"}),
    ]

    deltas = build_deltas(events)

    assert len(deltas.findings) == 1
    assert deltas.findings[0].finding_id == "f1"


def test_build_deltas_ignores_finding_resolved_with_empty_id() -> None:
    """When finding_id is empty in FINDING_RESOLVED, it is skipped."""
    events = [
        _event(1, EventKind.FINDING_RAISED, {"finding_id": "f1", "text": "real"}),
        _event(2, EventKind.FINDING_RESOLVED, {"finding_id": ""}),  # Empty, should be ignored
        _event(3, EventKind.FINDING_RESOLVED, {"finding_id": "f1"}),
    ]

    deltas = build_deltas(events)

    assert len(deltas.findings) == 1
    assert deltas.findings[0].resolved is True


def test_build_deltas_handles_finding_resolved_before_raised() -> None:
    """When a finding is resolved before being raised, it's tracked but not in findings_map yet."""
    events = [
        _event(1, EventKind.FINDING_RESOLVED, {"finding_id": "f1"}),  # Resolved first
        _event(2, EventKind.FINDING_RAISED, {"finding_id": "f1", "text": "late"}),
    ]

    deltas = build_deltas(events)

    # The finding should appear and be marked as resolved
    assert len(deltas.findings) == 1
    assert deltas.findings[0].finding_id == "f1"
    assert deltas.findings[0].resolved is True


def test_answer_why_question_includes_assumptions_in_search() -> None:
    """answer_why_question searches both decisions and assumptions."""
    events = [
        _event(
            1,
            EventKind.DECISION_RECORDED,
            {
                "decision_id": "d1",
                "title": "Use PostgreSQL",
                "choice": "postgres",
                "rationale": "ACID compliance",
            },
        ),
        _event(
            2,
            EventKind.ASSUMPTION_STATED,
            {"assumption_id": "a1", "text": "Traffic will be under 1000 requests per second"},
        ),
    ]

    # Question matching the decision
    answer = answer_why_question(events, "Why PostgreSQL?")
    assert "postgres" in answer.lower() or "decision" in answer.lower()

    # Question matching the assumption
    answer2 = answer_why_question(events, "What about traffic?")
    assert (
        "traffic" in answer2.lower() or "1000" in answer2.lower() or "assumption" in answer2.lower()
    )

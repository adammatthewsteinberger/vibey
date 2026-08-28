# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import UTC, datetime
from uuid import uuid4

from hypothesis import given
from hypothesis import strategies as st

from vibey.domain.briefing import build_deterministic_brief
from vibey.domain.handoff import BudgetSnapshot, LedgerRef, QuestionRef
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event, digest_range
from vibey.domain.noloss import verify
from vibey.domain.phase import Phase

PROJECT_ID = uuid4()
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _event(seq: int, kind: EventKind, payload: dict[str, object]) -> LedgerEvent:
    return LedgerEvent(
        event_id=uuid4(),
        project_id=PROJECT_ID,
        cycle=1,
        phase=Phase.BUILD,
        seq=seq,
        kind=kind,
        engine_id=None,
        job_id=None,
        causation_id=None,
        correlation_id=uuid4(),
        provenance=Provenance.AGENT,
        produced_at=NOW,
        payload=payload,
        digest=digest_event(payload),
    )


def _ref_for(events: list[LedgerEvent]) -> LedgerRef:
    if not events:
        return LedgerRef(uri="u", from_seq=0, to_seq=0, event_count=0, digest=digest_range(()))
    return LedgerRef(
        uri="u",
        from_seq=min(e.seq for e in events),
        to_seq=max(e.seq for e in events),
        event_count=len(events),
        digest=digest_range(events),
    )


ZERO_BUDGET = BudgetSnapshot(turns_spent=0, dollars_spent=0.0, max_turns=None, max_dollars=None)


def test_empty_ledger_produces_a_passing_brief() -> None:
    brief = build_deterministic_brief([])
    result = verify(ledger=[], brief=brief, ref=_ref_for([]), budget=ZERO_BUDGET)
    assert result.ok


def test_open_question_is_carried_verbatim_by_id() -> None:
    events = [
        _event(
            1, EventKind.QUESTION_ASKED, {"question_id": "q1", "text": "capped?", "blocking": True}
        )
    ]
    brief = build_deterministic_brief(events)

    assert brief.open_questions == (QuestionRef("q1", "capped?", blocking=True),)
    result = verify(ledger=events, brief=brief, ref=_ref_for(events), budget=ZERO_BUDGET)
    assert result.ok


def test_answered_question_is_not_carried() -> None:
    events = [
        _event(1, EventKind.QUESTION_ASKED, {"question_id": "q1", "text": "?", "blocking": False}),
        _event(2, EventKind.ANSWER_GIVEN, {"question_id": "q1", "text": "yes"}),
    ]
    brief = build_deterministic_brief(events)
    assert brief.open_questions == ()


def test_superseded_decision_is_not_carried_but_current_one_is() -> None:
    events = [
        _event(
            1, EventKind.DECISION_RECORDED, {"decision_id": "d1", "title": "old", "choice": "a"}
        ),
        _event(
            2,
            EventKind.DECISION_RECORDED,
            {"decision_id": "d2", "title": "new", "choice": "b", "supersedes": "d1"},
        ),
    ]
    brief = build_deterministic_brief(events)
    ids = {d.decision_id for d in brief.decisions}
    assert ids == {"d2"}


def test_remaining_work_from_latest_verdict_is_carried() -> None:
    events = [
        _event(1, EventKind.VERDICT_RENDERED, {"complete": False, "remaining_work": ["stale"]}),
        _event(2, EventKind.VERDICT_RENDERED, {"complete": False, "remaining_work": ["fresh"]}),
    ]
    brief = build_deterministic_brief(events)
    assert [r.text for r in brief.remaining] == ["fresh"]
    assert brief.next_action == "fresh"


def test_next_action_defaults_when_nothing_remaining() -> None:
    brief = build_deterministic_brief([])
    assert brief.next_action == "Review and accept."


def test_referenced_artifact_is_carried_unreferenced_is_not() -> None:
    events = [
        _event(
            1,
            EventKind.ARTIFACT_PRODUCED,
            {"artifact_id": "art1", "path": "x.sql", "referenced_by_open_item": True},
        ),
        _event(
            2,
            EventKind.ARTIFACT_PRODUCED,
            {"artifact_id": "art2", "path": "y.sql", "referenced_by_open_item": False},
        ),
    ]
    brief = build_deterministic_brief(events)
    ids = {a.artifact_id for a in brief.artifacts}
    assert ids == {"art1"}


def test_spec_constraints_are_carried_verbatim() -> None:
    brief = build_deterministic_brief([], spec_constraints=("must work offline",))
    assert brief.constraints == ("must work offline",)


def test_finding_with_unknown_severity_falls_back_to_low() -> None:
    events = [
        _event(
            1, EventKind.FINDING_RAISED, {"finding_id": "f1", "severity": "nonsense", "text": "x"}
        )
    ]
    brief = build_deterministic_brief(events)
    assert brief.open_findings[0].severity.value == "low"


def test_finding_with_unknown_ambiguity_falls_back_to_clear() -> None:
    events = [
        _event(
            1,
            EventKind.FINDING_RAISED,
            {"finding_id": "f1", "severity": "high", "text": "x", "ambiguity": "nonsense"},
        )
    ]
    brief = build_deterministic_brief(events)
    assert brief.open_findings[0].ambiguity.value == "clear"


# --- The property that matters: the floor is provably lossless --------------


def _closable_events_strategy() -> st.SearchStrategy[list[LedgerEvent]]:
    def build(
        n_open_q: int,
        n_answered_q: int,
        n_open_d: int,
        n_open_a: int,
        n_open_f: int,
        n_resolved_f: int,
    ) -> list[LedgerEvent]:
        events: list[LedgerEvent] = []
        seq = 1
        for i in range(n_open_q):
            events.append(
                _event(
                    seq,
                    EventKind.QUESTION_ASKED,
                    {"question_id": f"q{i}", "text": f"q{i}?", "blocking": False},
                )
            )
            seq += 1
        for i in range(n_answered_q):
            qid = f"aq{i}"
            events.append(
                _event(
                    seq,
                    EventKind.QUESTION_ASKED,
                    {"question_id": qid, "text": "x", "blocking": False},
                )
            )
            seq += 1
            events.append(
                _event(seq, EventKind.ANSWER_GIVEN, {"question_id": qid, "text": "answered"})
            )
            seq += 1
        for i in range(n_open_d):
            events.append(
                _event(
                    seq,
                    EventKind.DECISION_RECORDED,
                    {"decision_id": f"d{i}", "title": f"t{i}", "choice": "c"},
                )
            )
            seq += 1
        for i in range(n_open_a):
            events.append(
                _event(
                    seq,
                    EventKind.ASSUMPTION_STATED,
                    {"assumption_id": f"a{i}", "text": f"assume {i}", "confidence": "high"},
                )
            )
            seq += 1
        for i in range(n_open_f):
            events.append(
                _event(
                    seq,
                    EventKind.FINDING_RAISED,
                    {"finding_id": f"f{i}", "severity": "low", "text": "x"},
                )
            )
            seq += 1
        for i in range(n_resolved_f):
            fid = f"rf{i}"
            events.append(
                _event(
                    seq,
                    EventKind.FINDING_RAISED,
                    {"finding_id": fid, "severity": "low", "text": "x"},
                )
            )
            seq += 1
            events.append(
                _event(seq, EventKind.FINDING_RESOLVED, {"finding_id": fid, "resolution": "fixed"})
            )
            seq += 1
        events.append(
            _event(
                seq,
                EventKind.VERDICT_RENDERED,
                {"complete": False, "remaining_work": ["keep going"]},
            )
        )
        return events

    small_int = st.integers(0, 3)
    return st.builds(
        build,
        n_open_q=small_int,
        n_answered_q=small_int,
        n_open_d=small_int,
        n_open_a=small_int,
        n_open_f=small_int,
        n_resolved_f=small_int,
    )


@given(events=_closable_events_strategy())
def test_deterministic_brief_always_passes_the_gate(events: list[LedgerEvent]) -> None:
    brief = build_deterministic_brief(events)
    result = verify(ledger=events, brief=brief, ref=_ref_for(events), budget=ZERO_BUDGET)
    assert result.ok, result.violations
